import asyncio
from pathlib import Path
from typing import Optional, Tuple
from telethon.tl.types import Message, MessageMediaWebPage
from telethon.errors import FloodWaitError, TimeoutError as TelegramTimeoutError
from . import utils
from .settings import DelaySettings


class MediaHandler:
    def __init__(self, media_folder: Path, delay_settings: DelaySettings):
        self.media_folder = media_folder
        self.delay_settings = delay_settings

    async def download(self, msg: Message, pbar=None) -> Optional[Tuple[str, str]]:
        for attempt in range(self.delay_settings.max_retries):
            try:
                media_type, ext, suggested_name = "document", "bin", None

                if getattr(msg, 'photo', None):
                    media_type, ext = "photo", "jpg"
                elif getattr(msg, 'document', None):
                    mime = getattr(msg.document, 'mime_type', '') or ''
                    mt = mime.lower()
                    if mt.startswith('image'):
                        media_type = 'photo'
                    elif mt.startswith('video'):
                        media_type = 'video'
                    elif mt.startswith('audio'):
                        media_type = 'audio'
                    else:
                        media_type = 'document'
                    try:
                        ext = mt.split('/')[-1] or ext
                    except:
                        pass
                    try:
                        for a in getattr(msg.document, 'attributes', []):
                            if getattr(a, 'file_name', None):
                                suggested_name = utils.sanitize_filename(a.file_name)
                                break
                    except:
                        pass
                elif isinstance(msg.media, MessageMediaWebPage):
                    try:
                        wp = msg.media.webpage
                        if getattr(wp, 'photo', None):
                            media_type, ext = 'photo', 'jpg'
                        else:
                            media_type, ext = 'document', 'html'
                    except:
                        media_type, ext = 'document', 'html'
                else:
                    media_type = 'document'

                target_folder = self.media_folder / media_type
                target_folder.mkdir(parents=True, exist_ok=True)

                if suggested_name:
                    filename = suggested_name
                    if not Path(filename).suffix: filename = f"{filename}.{ext}"
                else:
                    filename = f"{media_type}_{msg.id}.{ext}"

                filepath = target_folder / filename
                counter = 1
                while filepath.exists():
                    name, suffix = Path(filename).stem, Path(filename).suffix
                    filepath = target_folder / f"{name}_{counter}{suffix}"
                    counter += 1

                last_percent = -1

                def callback(current, total):
                    nonlocal last_percent
                    if total > 0:
                        percent = int((current / total) * 100)
                        if percent > last_percent:
                            last_percent = percent
                            if pbar: pbar.set_postfix_str(f"Downloading media ({percent}%)")

                saved_path = await msg.download_media(file=str(filepath), progress_callback=callback)
                if pbar: pbar.set_postfix_str("")
                await asyncio.sleep(self.delay_settings.delay_between_media)

                if not saved_path: return None
                saved_path = Path(saved_path)
                saved_ext = saved_path.suffix.lower().lstrip('.')
                if saved_ext in ('jpg', 'jpeg', 'png', 'webp', 'gif'):
                    media_type = 'photo'
                elif saved_ext in ('mp4', 'mov', 'webm', 'mkv', 'avi'):
                    media_type = 'video'
                elif saved_ext in ('mp3', 'wav', 'ogg', 'm4a', 'flac'):
                    media_type = 'audio'

                return f"media/{media_type}/{saved_path.name}", media_type

            except (FloodWaitError, TelegramTimeoutError, TimeoutError) as e:
                if attempt < self.delay_settings.max_retries - 1:
                    wait_time = self.delay_settings.retry_delay * (attempt + 1)
                    if isinstance(e, FloodWaitError): wait_time = max(wait_time, e.seconds)
                    if pbar: pbar.set_postfix_str(f"error, retry in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    if pbar: pbar.set_postfix_str("failed, skipping...")
                    return None
            except Exception:
                if pbar: pbar.set_postfix_str("failed, skipping...")
                return None
        return None
