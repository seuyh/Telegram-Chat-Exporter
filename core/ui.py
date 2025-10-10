from typing import List, Optional
from telethon.tl.types import User, Chat, Channel
from .client_manager import ClientManager
from .settings import DelaySettings
from .exporter import ChatExporter
from .merger import Merger
from datetime import datetime
from pathlib import Path


class AppUI:
    def __init__(self):
        self.client_manager = ClientManager()
        self.delay_settings = DelaySettings()
        self.client = None

    def show_banner(self):
        print("\n" + "=" * 60)
        print("  📥 TELEGRAM CHAT EXPORTER")
        print("  Export chats and channels to beautiful HTML")
        print("=" * 60 + "\n")

    async def start(self):
        self.show_banner()
        while True:
            action = await self._show_session_menu()

            if action == 'exit':
                print("\n👋 Goodbye!")
                break
            elif action == 'create':
                await self.client_manager.create_new_session()
            elif action == 'merge':
                await self.run_merger()
            elif action:
                session_name = action
                self.client = await self.client_manager.get_client(session_name)
                if self.client:
                    await self.main_menu()
                    await self.client.disconnect()

    async def _show_session_menu(self) -> str:
        print("🔐 SESSIONS:")
        session_files = self.client_manager.get_session_files()

        if not session_files:
            print("   No saved sessions found.")

        for idx, file in enumerate(session_files, 1):
            print(f"   {idx}. 📂 {file.stem}")

        print("-" * 20)
        print(f"   a. ➕ Add new session")
        print(f"   u. 🖇️ Unite two exports")
        print(f"   e. 🚪 Exit")

        while True:
            options = "a, u, e"
            if session_files:
                options = f"1-{len(session_files)}, " + options
            prompt = f"Choose action ({options}): "
            choice = input(f"\n{prompt}").strip().lower()

            if choice == 'a': return 'create'
            if choice == 'u': return 'merge'
            if choice == 'e': return 'exit'

            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(session_files):
                    return session_files[choice_num - 1].stem
                else:
                    print(f"❌ Enter a number from 1 to {len(session_files)}")
            except (ValueError, IndexError):
                print(f"❌ Please enter a valid choice.")

    async def main_menu(self):
        while True:
            print("\n" + "=" * 60 + "\n📋 MAIN MENU:")
            print(
                "1. 📋 Show all chats\n2. 🔍 Search chat\n3. 🆔 Export by ID\n4. ⚙️ Settings\nb. ⬅️ Back to session select")
            choice = input("\nChoose action (1-5): ").strip()
            if choice == "1":
                await self.show_all_chats()
            elif choice == "2":
                await self.search_chat()
            elif choice == "3":
                await self.export_by_id()
            elif choice == "4":
                self.delay_settings.configure()
            elif choice == "b":
                break
            else:
                print("❌ Invalid choice!")

    async def show_all_chats(self):
        print("\n⏳ Loading chat list...")
        dialogs = await self.client.get_dialogs()
        chats = {'channels': [], 'groups': [], 'private': []}
        for d in dialogs:
            if isinstance(d.entity, Channel):
                chats['channels' if d.entity.broadcast else 'groups'].append(d)
            elif isinstance(d.entity, Chat):
                chats['groups'].append(d)
            elif isinstance(d.entity, User) and not d.entity.bot:
                chats['private'].append(d)

        while True:
            print("\n" + "=" * 60 + "\n📱 CHAT TYPES:")
            print(f"1. 📢 Channels ({len(chats['channels'])})\n2. 👥 Groups ({len(chats['groups'])})")
            print(f"3. 💬 Private chats ({len(chats['private'])})\nb. ⬅️ Back")
            choice = input("\nChoose type (1-4): ").strip()
            if choice == "1":
                await self.select_from_list(chats['channels'], "CHANNELS")
            elif choice == "2":
                await self.select_from_list(chats['groups'], "GROUPS")
            elif choice == "3":
                await self.select_from_list(chats['private'], "PRIVATE CHATS")
            elif choice == "b":
                break
            else:
                print("❌ Invalid choice!")

    async def select_from_list(self, dialogs: List, title: str):
        if not dialogs: print(f"\n❌ No available: {title}"); return
        page, page_size = 0, 20
        while True:
            total_pages = (len(dialogs) - 1) // page_size + 1
            start_idx, end_idx = page * page_size, min((page + 1) * page_size, len(dialogs))
            print(f"\n{'=' * 60}\n📋 {title} (page {page + 1}/{total_pages}):\n{'=' * 60}")

            for i, d in enumerate(dialogs[start_idx:end_idx], 1):
                name = self._get_formatted_name_for_ui(d.entity)
                print(f"{start_idx + i}. {name}")

            print(f"\n{'=' * 60}")
            print("  [number] - export chat")
            if page > 0: print("  [p] - previous page")
            if page < total_pages - 1: print("  [n] - next page")
            print("  [b] - back to previous menu")
            cmd = input("\nEnter command: ").strip().lower()

            if cmd == 'b':
                break
            elif cmd == 'n' and page < total_pages - 1:
                page += 1
            elif cmd == 'p' and page > 0:
                page -= 1
            else:
                try:
                    choice_num = int(cmd)
                    if 1 <= choice_num <= len(dialogs):
                        await self.export_chat_interactive(dialogs[choice_num - 1].entity)
                    else:
                        print(f"❌ Enter number from 1 to {len(dialogs)}")
                except (ValueError, IndexError):
                    print("❌ Invalid command!")

    def _get_formatted_name_for_ui(self, entity):
        if isinstance(entity, User):
            name_parts = []
            if first_name := getattr(entity, 'first_name', None): name_parts.append(first_name)
            if last_name := getattr(entity, 'last_name', None): name_parts.append(last_name)
            name = " ".join(name_parts).strip() or "Deleted Account"
            if username := getattr(entity, 'username', None): name += f" [@{username}]"
            return name
        else:
            return getattr(entity, 'title', "Unknown")

    async def search_chat(self):
        query = input("\n🔍 Enter chat name (or press Enter to cancel): ").strip()
        if not query: return
        print(f"\n⏳ Searching '{query}'...")
        dialogs = await self.client.get_dialogs()
        found = [d for d in dialogs if query.lower() in d.name.lower()]
        if not found:
            print(f"❌ Nothing found for '{query}'")
            return
        await self.select_from_list(found, f"SEARCH RESULTS '{query}'")

    async def export_by_id(self):
        print("\n🆔 EXPORT BY ID/USERNAME (e.g., @durov, -100123..., +7...)")
        chat_id = input("Enter ID (or press Enter to cancel): ").strip()
        if not chat_id: return

        entity = None
        print(f"\n⏳ Searching '{chat_id}'...")

        try:
            if chat_id.replace('-', '').isdigit():
                entity_id = int(chat_id)
                dialogs = await self.client.get_dialogs()
                for d in dialogs:
                    if d.id == entity_id:
                        entity = d.entity
                        break
                if not entity: entity = await self.client.get_entity(entity_id)
            else:
                entity = await self.client.get_entity(chat_id)

            if not entity:
                print("❌ Unable to resolve entity. Ensure you are a member of the chat.")
                return

            name = self._get_formatted_name_for_ui(entity)
            type_icon = "❓"
            if isinstance(entity, User):
                type_icon = "💬"
            elif isinstance(entity, Channel):
                type_icon = "📢" if entity.broadcast else "👥"
            elif isinstance(entity, Chat):
                type_icon = "👥"

            print(f"\n✅ Entity found: {type_icon} {name}")
            confirm_found = input("   Is this correct? [Y/n]: ").strip().lower()

            if confirm_found != 'n':
                await self.export_chat_interactive(entity)
            else:
                print("❌ Operation cancelled. Returning to main menu.")

        except Exception as e:
            print(f"❌ Error: {e}")
            print("💡 Check if the ID/username is correct or if you have access to the chat.")

    async def export_chat_interactive(self, entity):
        name = self._get_formatted_name_for_ui(entity)
        print(f"\n{'=' * 60}\n📥 EXPORT: {name}\n{'=' * 60}")
        download_media = input("\n📥 Download media files? [Y/n]: ").strip().lower() != 'n'
        max_file_size = None
        append_folder_path = None

        if download_media:
            while True:
                try:
                    max_size_mb_str = input("Enter max file size in MB (leave empty for no limit): ").strip().replace(
                        ',', '.')
                    if max_size_mb_str:
                        max_file_size = float(max_size_mb_str)
                        break
                    else:
                        max_file_size = None
                        break
                except ValueError:
                    print("❌ Invalid input! Please enter a number (e.g., 50, 2.5, 0.5) or leave empty.")

        start_date, end_date = None, None
        while True:
            try:
                start_date_str = input(
                    "\nEnter start date (YYYY-MM-DD HH:MM, UTC) or [a] to append to existing export (optional, press Enter to skip): ").strip().lower()

                if not start_date_str:
                    start_date = None
                elif start_date_str == 'a':
                    append_folder_path = await self._select_export_folder("Select an export to append to")
                    if append_folder_path:
                        print(f"\n⏳ Analyzing '{append_folder_path.name}' to find the last message date...")
                        last_date = Merger.get_last_message_date(append_folder_path)
                        if last_date:
                            start_date = last_date
                            print(
                                f"✅ Start date set to {start_date.strftime('%Y-%m-%d %H:%M')} UTC from the last message.")
                        else:
                            print(f"❌ Could not find any messages in '{append_folder_path.name}'. Append cancelled.")
                            append_folder_path = None
                    else:
                        print("Append cancelled.")
                        continue
                else:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M')

                end_date_str = input("Enter end date (YYYY-MM-DD HH:MM, UTC) (optional, press Enter to skip): ").strip()
                if end_date_str:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M')
                else:
                    end_date = None
                break
            except ValueError:
                print("❌ Invalid date format! Please use YYYY-MM-DD HH:MM.")
            except ImportError:
                print("\n❌ Error: Missing required libraries for this feature.")
                print("   Please install them by running: pip install beautifulsoup4 lxml")

        print(f"\n✅ READY TO EXPORT:\n   Chat: {name}\n   Media: {'yes' if download_media else 'no'}")
        if download_media and max_file_size is not None:
            print(f"   Max file size: {max_file_size} MB")
        if start_date:
            print(f"   From date: {start_date.strftime('%Y-%m-%d %H:%M')} UTC")
        if end_date:
            print(f"   To date:   {end_date.strftime('%Y-%m-%d %H:%M')} UTC")
        if append_folder_path:
            print(f"   Mode:      Append to '{append_folder_path.name}'")

        confirm = input("\n▶️ Start export? [Y/n]: ").strip().lower()

        if confirm != 'n':
            exporter = ChatExporter(self.client, self.delay_settings)
            await exporter.export_chat(entity, download_media, max_file_size, start_date, end_date)

            if append_folder_path and exporter.export_folder:
                print("\n" + "=" * 60)
                print("🖇️ APPEND MODE: Automatically merging new export...")
                print(f"   Original: {append_folder_path.name}")
                print(f"   New data: {exporter.export_folder.name}")
                print("=" * 60)
                try:
                    merger = Merger(str(append_folder_path), str(exporter.export_folder))
                    merger.merge()
                except Exception as e:
                    print(f"\n❌ An unexpected error occurred during auto-merge: {e}")
        else:
            print("❌ Export cancelled. Returning to main menu.")

    async def _select_export_folder(self, prompt: str, exclude: Path = None) -> Path | None:
        print(f"\n{'=' * 60}\n{prompt}\n")
        exports_dir = Path("exports")
        valid_exports = []

        if exports_dir.is_dir():
            valid_exports = sorted([
                d for d in exports_dir.iterdir()
                if d.is_dir() and (d / "messages.html").is_file()
            ])

        if valid_exports:
            for i, folder in enumerate(valid_exports, 1):
                if folder == exclude:
                    print(f"   {i}. 📁 {folder.name} [selected]")
                else:
                    print(f"   {i}. 📁 {folder.name}")
            print("-" * 20)
        else:
            print("   No exports found in the 'exports' directory.")

        print("   [c] - Enter a custom path")
        print("   [b] - Back")

        while True:
            choice = input("\nChoose an option: ").strip().lower()
            if choice == 'b': return None
            if choice == 'c':
                return await self._prompt_for_custom_path_loop(exclude=exclude)

            try:
                num = int(choice)
                if 1 <= num <= len(valid_exports):
                    selected = valid_exports[num - 1]
                    if selected == exclude:
                        print("❌ This folder is already selected. Please choose a different one.")
                        continue
                    return selected
                else:
                    print(f"❌ Please enter a number between 1 and {len(valid_exports)}.")
            except (ValueError, IndexError):
                print("❌ Invalid input. Please enter a number or a letter from the options.")

    async def _prompt_for_custom_path_loop(self, exclude: Path = None) -> Path | None:
        while True:
            path_str = input("\nEnter the full path to an export folder (or press Enter to go back): ").strip()
            if not path_str: return None

            path = Path(path_str)
            if path == exclude:
                print("❌ This folder is already selected. Please choose a different one.")
                continue

            if path.is_dir() and (path / "messages.html").is_file():
                return path
            else:
                print("❌ Path is not a valid export folder (must contain messages.html).")

    async def run_merger(self):
        print("\n" + "=" * 60)
        print("🖇️ UNITE TWO EXPORTS")
        print("=" * 60)

        folder1 = await self._select_export_folder("Select the FIRST export folder to merge")
        if not folder1:
            print("Operation cancelled.")
            return

        folder2 = await self._select_export_folder("Select the SECOND export folder to merge", exclude=folder1)
        if not folder2:
            print("Operation cancelled.")
            return

        print(f"\n✅ Folders selected for merging:\n   1: {folder1.name}\n   2: {folder2.name}")
        confirm = input("\n▶️ Start merge? [Y/n]: ").strip().lower()
        if confirm == 'n':
            print("❌ Merge cancelled.")
            return

        try:
            merger = Merger(str(folder1), str(folder2))
            merger.merge()
        except ImportError:
            print("\n❌ Error: Missing required libraries for merging.")
            print("   Please install them by running: pip install beautifulsoup4 lxml")
        except Exception as e:
            print(f"\n❌ An unexpected error occurred: {e}")