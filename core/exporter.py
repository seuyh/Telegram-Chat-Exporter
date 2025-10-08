import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from peewee import (Model, SqliteDatabase, TextField, DateTimeField, Proxy, IntegerField)
from telethon import TelegramClient
from telethon.tl.types import (User, Chat, Channel, Message, MessageActionChannelCreate,
                               MessageActionChatAddUser, MessageActionChatDeleteUser,
                               MessageActionChatJoinedByLink, MessageActionPinMessage)
from tqdm.asyncio import tqdm as async_tqdm

from . import utils
from .html_generator import HtmlGenerator
from .media_handler import MediaHandler
from .settings import DelaySettings

db_proxy = Proxy()


class MessageModel(Model):
    telegram_message_id = IntegerField(primary_key=True)
    grouped_id = IntegerField(null=True)
    date = DateTimeField()
    sender = TextField(null=True)
    text = TextField(null=True)
    reply_to = TextField(null=True)
    forwarded_from = TextField(null=True)
    media_path = TextField(null=True)
    media_type = TextField(null=True)
    media_placeholder = TextField(null=True)
    action_text = TextField(null=True)

    class Meta:
        database = db_proxy


class ChatExporter:
    def __init__(self, client: TelegramClient, delay_settings: DelaySettings):
        self.client = client
        self.delay_settings = delay_settings
        self.export_folder = None
        self.media_folder = None
        self.db_path = None
        self.db = None

    def _init_db(self):
        self.db_path = self.export_folder / f"temp_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        self.db = SqliteDatabase(self.db_path)
        db_proxy.initialize(self.db)
        self.db.connect()
        self.db.create_tables([MessageModel])

    async def export_chat(self, entity, download_media: bool, max_file_size: Optional[float] = None):
        chat_name = self._get_entity_name(entity)
        safe_name = utils.sanitize_filename(chat_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.export_folder = Path(f"exports/{safe_name}_{timestamp}")
        self.export_folder.mkdir(parents=True, exist_ok=True)

        if download_media:
            self.media_folder = self.export_folder / "media"
            self.media_folder.mkdir(exist_ok=True)

        try:
            self._init_db()
            print(
                f"\n{'=' * 60}\n📥 EXPORT STARTED\n📁 Folder: {self.export_folder}\n{'=' * 60}")

            total_messages = await self._data_ingestion_pass(entity, download_media, max_file_size)
            self._html_generation_pass(chat_name, total_messages)

            print(
                f"\n{'=' * 60}\n✨ EXPORT COMPLETED!\n📄 File: {(self.export_folder / 'messages.html').absolute()}\n📊 Messages: {total_messages}")
            if download_media and self.media_folder:
                media_count = sum(1 for f in (self.export_folder / "media").rglob('*') if f.is_file())
                print(f"🖼️ Media files: {media_count}")
            print("=" * 60)
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print("💡 Check if the ID/username is correct or if you have access to the chat.")
        finally:
            if self.db and not self.db.is_closed():
                self.db.close()
            if self.db_path and self.db_path.exists():
                try:
                    os.remove(self.db_path)
                except OSError as e:
                    print(f"\n⚠️ Warning: Could not delete temporary database '{self.db_path}'.")
                    print(f"   Reason: {e}. You can safely delete this file manually.")

    async def _data_ingestion_pass(self, entity, download_media: bool, max_file_size: Optional[float]) -> int:
        print("\n⏳ Loading messages and media into database...")
        media_handler = MediaHandler(self.media_folder, self.delay_settings,
                                     max_file_size) if download_media else None

        total = await self.client.get_messages(entity, limit=0)
        pbar = async_tqdm(total=total.total, desc="Exporting", unit=" msg", colour='cyan')

        message_count = 0
        batch = []
        BATCH_SIZE = 200

        async for msg in self.client.iter_messages(entity):
            if not msg: continue

            data_dict = await self._process_message_for_db(msg, media_handler, pbar)
            batch.append({
                'telegram_message_id': msg.id,
                'grouped_id': msg.grouped_id,
                'date': msg.date,
                'sender': data_dict.get('from'),
                'text': data_dict.get('text'),
                'reply_to': json.dumps(data_dict.get('reply_to')),
                'forwarded_from': json.dumps(data_dict.get('forwarded')),
                'media_path': data_dict.get('media_path'),
                'media_type': data_dict.get('media_type'),
                'media_placeholder': data_dict.get('media_placeholder'),
                'action_text': data_dict.get('action_text')
            })

            if len(batch) >= BATCH_SIZE:
                MessageModel.insert_many(batch).execute()
                batch.clear()

            message_count += 1
            pbar.update(1)
            await asyncio.sleep(self.delay_settings.delay_between_messages)

        if batch:
            MessageModel.insert_many(batch).execute()
            batch.clear()

        pbar.close()
        print(f"\n✅ All {message_count} messages saved to database.")
        return message_count

    def _html_generation_pass(self, chat_name: str, total_messages: int):
        print(f"\n📄 Generating HTML from database...")

        messages_map = {}
        query = MessageModel.select().order_by(MessageModel.date.asc())

        for msg_record in query:
            key = msg_record.grouped_id if msg_record.grouped_id else msg_record.telegram_message_id

            if key not in messages_map:
                msg_date = msg_record.date
                if isinstance(msg_date, str):
                    msg_date = datetime.fromisoformat(msg_date)

                messages_map[key] = {
                    'date': msg_date,
                    'from': msg_record.sender,
                    'text': msg_record.text,
                    'reply_to': json.loads(msg_record.reply_to) if msg_record.reply_to else None,
                    'forwarded': json.loads(msg_record.forwarded_from) if msg_record.forwarded_from else None,
                    'media_files': [],
                    'media_placeholder': msg_record.media_placeholder,
                    'action_text': msg_record.action_text
                }

            if msg_record.text:
                messages_map[key]['text'] = msg_record.text

            if msg_record.media_path:
                messages_map[key]['media_files'].append({
                    'path': msg_record.media_path,
                    'type': msg_record.media_type
                })

        processed_messages = list(messages_map.values())

        processed_messages = [
            msg for msg in processed_messages
            if msg.get('text') or msg.get('media_files') or msg.get('action_text') or msg.get('media_placeholder')
        ]

        generator = HtmlGenerator(chat_name, processed_messages)
        html_content = generator.generate()
        html_file = self.export_folder / "messages.html"
        html_file.write_text(html_content, encoding='utf-8')

    async def _process_message_for_db(self, msg: Message, media_handler: Optional[MediaHandler], pbar) -> dict:
        data = {'from': await self._get_sender_name(msg), 'text': utils.format_text(msg.text or ''), }

        if msg.action:
            data['action_text'] = await self._format_message_action(msg)

        if msg.media:
            if media_handler:
                result = await media_handler.download(msg, pbar)
                if result:
                    data['media_path'], data['media_type'] = result
                else:
                    data['media_placeholder'] = self._get_media_placeholder(msg)
            else:
                data['media_placeholder'] = self._get_media_placeholder(msg)

        if msg.reply_to and getattr(msg.reply_to, 'reply_to_msg_id', None):
            try:
                reply_msg = await msg.get_reply_message()
                if reply_msg:
                    data['reply_to'] = {'text': reply_msg.text or '', 'from': await self._get_sender_name(reply_msg)}
            except:
                pass

        if msg.forward:
            fwd_from = 'Unknown'
            try:
                if msg.forward.from_name:
                    fwd_from = msg.forward.from_name
                elif msg.forward.from_id:
                    fwd_entity = await self.client.get_entity(msg.forward.from_id)
                    fwd_from = self._get_entity_name(fwd_entity)
            except:
                pass
            data['forwarded'] = {'from': fwd_from}
        return data

    async def _get_sender_name(self, msg: Message) -> str:
        try:
            sender = await msg.get_sender()
            return self._get_entity_name(sender)
        except:
            return "Unknown"

    def _get_entity_name(self, entity) -> str:
        if isinstance(entity, User):
            name_parts = []
            if first_name := getattr(entity, 'first_name', None): name_parts.append(first_name)
            if last_name := getattr(entity, 'last_name', None): name_parts.append(last_name)
            full_name = " ".join(name_parts).strip() or "Deleted Account"
            if username := getattr(entity, 'username', None): return f"{full_name} [@{username}]"
            return full_name
        elif isinstance(entity, (Chat, Channel)):
            return entity.title or "Unknown"
        return "Unknown"

    def _get_media_placeholder(self, msg: Message) -> str:
        if msg.photo: return '[PHOTO]'
        if msg.video_note: return '[VIDEO MESSAGE]'
        if msg.video: return '[VIDEO]'
        if msg.voice: return '[VOICE MESSAGE]'
        if msg.audio: return '[AUDIO FILE]'
        if msg.sticker: return '[STICKER]'
        if msg.document:
            mime_type = getattr(msg.document, 'mime_type', '').lower()
            if 'gif' in mime_type: return '[GIF]'
            return '[DOCUMENT]'
        return '[MEDIA]'

    async def _format_message_action(self, msg: Message) -> Optional[str]:
        action = msg.action
        actor_name = await self._get_sender_name(msg)
        if isinstance(action, MessageActionChannelCreate): return f'Channel "{action.title}" was created'
        if isinstance(action, MessageActionChatAddUser): return f'"{actor_name}" added a new member'
        if isinstance(action, MessageActionChatDeleteUser): return f'"{actor_name}" removed a member'
        if isinstance(action, MessageActionChatJoinedByLink): return f'"{actor_name}" joined via invite link'
        if isinstance(action, MessageActionPinMessage): return 'A message was pinned'
        return "System Message"