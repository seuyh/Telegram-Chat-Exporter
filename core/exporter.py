import asyncio
import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from tqdm.asyncio import tqdm as async_tqdm
from telethon import TelegramClient
from telethon.tl.types import User, Chat, Channel, Message, MessageActionChannelCreate, \
    MessageActionChatAddUser, MessageActionChatDeleteUser, MessageActionChatJoinedByLink, MessageActionPinMessage

from . import utils
from .settings import DelaySettings
from .media_handler import MediaHandler
from .html_generator import HtmlGenerator


class ChatExporter:
    def __init__(self, client: TelegramClient, delay_settings: DelaySettings):
        self.client = client
        self.delay_settings = delay_settings
        self.export_folder = None
        self.media_folder = None
        self.db_path = None
        self.db_conn = None

    def _init_db(self):
        self.db_path = self.export_folder / f"temp_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        self.db_conn = sqlite3.connect(self.db_path)
        cursor = self.db_conn.cursor()
        cursor.execute('''
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                sender TEXT,
                text TEXT,
                reply_to TEXT,
                forwarded_from TEXT,
                media_path TEXT,
                media_type TEXT,
                media_placeholder TEXT,
                action_text TEXT
            )
        ''')
        self.db_conn.commit()

    async def export_chat(self, entity, download_media: bool, max_file_size: Optional[int] = None):
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
                media_count = sum(1 for f in self.export_folder.rglob('*') if f.is_file())
                print(f"🖼️ Media files: {media_count - 1}")
            print("=" * 60)

        finally:
            if self.db_conn:
                self.db_conn.close()
            if self.db_path and self.db_path.exists():
                try:
                    os.remove(self.db_path)
                except OSError as e:
                    print(f"\n⚠️ Warning: Could not delete temporary database '{self.db_path}'.")
                    print(f"   Reason: {e}. You can safely delete this file manually.")

    async def _data_ingestion_pass(self, entity, download_media: bool, max_file_size: Optional[int]) -> int:
        print("\n⏳ Loading messages and media into database...")
        media_handler = MediaHandler(self.media_folder, self.delay_settings, max_file_size) if download_media else None

        total = await self.client.get_messages(entity, limit=0)
        pbar = async_tqdm(total=total.total, desc="Exporting", unit=" msg", colour='cyan')

        message_count = 0
        async for msg in self.client.iter_messages(entity):
            if not msg: continue

            data_dict = await self._process_message_for_db(msg, media_handler, pbar)

            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO messages (date, sender, text, reply_to, forwarded_from, media_path, media_type, media_placeholder, action_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                msg.date.isoformat(),
                data_dict.get('from'),
                data_dict.get('text'),
                json.dumps(data_dict.get('reply_to')),
                json.dumps(data_dict.get('forwarded')),
                data_dict.get('media_path'),
                data_dict.get('media_type'),
                data_dict.get('media_placeholder'),
                data_dict.get('action_text')
            ))
            message_count += 1
            pbar.update(1)
            await asyncio.sleep(self.delay_settings.delay_between_messages)

        self.db_conn.commit()
        pbar.close()
        print(f"\n✅ All {message_count} messages saved to database.")
        return message_count

    def _html_generation_pass(self, chat_name: str, total_messages: int):
        print(f"\n📄 Generating HTML from database...")
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT * FROM messages ORDER BY date ASC")

        processed_messages = []
        for row in cursor.fetchall():
            processed_messages.append({
                'date': datetime.fromisoformat(row[1]),
                'from': row[2],
                'text': row[3],
                'reply_to': json.loads(row[4]) if row[4] else None,
                'forwarded': json.loads(row[5]) if row[5] else None,
                'media': row[6],
                'media_type': row[7],
                'media_placeholder': row[8],
                'action_text': row[9]
            })

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