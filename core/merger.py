import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup
from .html_generator import HtmlGenerator


class Merger:
    def __init__(self, path1: str, path2: str):
        self.path1 = Path(path1)
        self.path2 = Path(path2)
        self.html1_path = self.path1 / "messages.html"
        self.html2_path = self.path2 / "messages.html"

    def _validate_paths(self) -> bool:
        if not self.path1.is_dir() or not self.html1_path.is_file():
            print(f"❌ Error: Path 1 is not a valid export folder: {self.path1}")
            return False
        if not self.path2.is_dir() or not self.html2_path.is_file():
            print(f"❌ Error: Path 2 is not a valid export folder: {self.path2}")
            return False
        return True

    def merge(self):
        if not self._validate_paths():
            return

        print("\n⏳ Starting merge process...")
        try:
            print("   - Parsing first export...")
            messages1 = self._parse_html_file(self.html1_path)
            print("   - Parsing second export...")
            messages2 = self._parse_html_file(self.html2_path)

            print("   - Combining, removing duplicates, and sorting messages...")

            combined_messages = messages1
            combined_messages.update(messages2)

            all_messages = sorted(list(combined_messages.values()), key=lambda x: x['date'])

            if not all_messages:
                print("❌ No messages found to merge.")
                return

            self._generate_merged_export(all_messages)

        except Exception as e:
            print(f"❌ An error occurred during merge: {e}")
            import traceback
            traceback.print_exc()

    @staticmethod
    def _parse_html_file(html_path: Path) -> dict:
        messages = {}
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'lxml')

        current_date_str = None
        message_container = soup.find('div', class_='messages')
        if not message_container: return {}

        for element in message_container.children:
            if not hasattr(element, 'get'): continue

            classes = element.get('class', [])
            if 'date-separator' in classes:
                current_date_str = element.get_text(strip=True)
            elif 'message' in classes and current_date_str:
                msg_data = Merger._extract_message_data(element, current_date_str)
                if msg_data:
                    unique_key = f"{msg_data['date'].isoformat()}-{msg_data['from']}-{msg_data['text']}"
                    messages[unique_key] = msg_data
        return messages

    @staticmethod
    def _extract_message_data(tag, date_str: str) -> dict or None:
        time_tag = tag.find('span', class_='time')
        if not time_tag: return None
        time_str = time_tag.get_text(strip=True)

        try:
            dt_obj = datetime.strptime(f"{date_str} {time_str}", '%d %B %Y %H:%M')
        except ValueError:
            return None

        sender = (tag.find('span', class_='sender') or tag.find('div')).get_text(strip=True)
        text_tag = tag.find('div', class_='text')
        text_html = ''.join(str(c) for c in text_tag.contents).strip() if text_tag else ""

        media_files = []
        for media_div in tag.select('.media-group .media, .media-group .document-standalone'):
            img = media_div.select_one('img.media-item')
            video = media_div.select_one('video.media-item')
            audio = media_div.select_one('audio')
            doc = media_div.select_one('a.document-name')
            if img and img.get('src'): media_files.append({'path': img['src'], 'type': 'photo'})
            if video and video.get('src'): media_files.append({'path': video['src'], 'type': 'video'})
            if audio and audio.get('src'): media_files.append({'path': audio['src'], 'type': 'audio'})
            if doc and doc.get('href'): media_files.append({'path': doc['href'], 'type': 'document'})

        return {
            'date': dt_obj,
            'from': sender,
            'text': text_html,
            'media_files': media_files
        }

    def _generate_merged_export(self, messages: list):
        original_chat_name = self.path1.name.rsplit('_', 1)[0]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_folder_name = f"{original_chat_name}_merged_{timestamp}"
        new_export_path = Path(f"exports/{new_folder_name}")
        new_export_path.mkdir(parents=True, exist_ok=True)

        print("   - Copying media files...")
        self._copy_media_files(new_export_path)

        print("   - Generating new HTML file...")
        first_msg_date = messages[0]['date']
        last_msg_date = messages[-1]['date']

        generator = HtmlGenerator(original_chat_name, messages, first_msg_date, last_msg_date)
        html_content = generator.generate()
        html_file = new_export_path / "messages.html"
        html_file.write_text(html_content, encoding='utf-8')

        print(f"\n{'=' * 60}")
        print("✨ MERGE COMPLETED!")
        print(f"📄 File: {html_file.absolute()}")
        print(f"📊 Messages: {len(messages)}")
        print(f"{'=' * 60}")

    def _copy_media_files(self, new_export_path: Path):
        new_media_path = new_export_path / "media"
        new_media_path.mkdir(exist_ok=True)

        for src_path in [self.path1, self.path2]:
            src_media_path = src_path / "media"
            if not src_media_path.is_dir(): continue

            for media_type_dir in src_media_path.iterdir():
                if not media_type_dir.is_dir(): continue

                new_target_dir = new_media_path / media_type_dir.name
                new_target_dir.mkdir(exist_ok=True)

                for file in media_type_dir.iterdir():
                    dest_file = new_target_dir / file.name
                    if dest_file.exists():
                        counter = 1
                        while dest_file.exists():
                            dest_file = new_target_dir / f"{file.stem}_{counter}{file.suffix}"
                            counter += 1
                    shutil.copy(file, dest_file)

    @classmethod
    def get_last_message_date(cls, folder_path: Path) -> Optional[datetime]:
        html_path = folder_path / "messages.html"
        if not html_path.is_file():
            return None

        try:
            messages_dict = cls._parse_html_file(html_path)
            if not messages_dict:
                return None

            all_messages = sorted(list(messages_dict.values()), key=lambda x: x['date'])
            return all_messages[-1]['date']
        except Exception:
            return None