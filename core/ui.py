from typing import List
from telethon.tl.types import User, Chat, Channel
from .client_manager import ClientManager
from .settings import DelaySettings
from .exporter import ChatExporter


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
        print(f"   e. 🚪 Exit")

        while True:
            prompt = f"Choose action ({'1-' + str(len(session_files)) + ', ' if session_files else ''}a, e): "
            choice = input(f"\n{prompt}").strip().lower()

            if choice == 'a':
                return 'create'
            if choice == 'e':
                return 'exit'

            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(session_files):
                    return session_files[choice_num - 1].stem
                else:
                    print(f"❌ Enter a number from 1 to {len(session_files)}")
            except (ValueError, IndexError):
                print("❌ Please enter a valid number or letter (a, e).")

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

        if download_media:
            try:
                max_size_mb_str = input("Enter max file size in MB (leave empty for no limit): ").strip()
                if max_size_mb_str:
                    max_file_size = int(max_size_mb_str)
            except ValueError:
                print("❌ Invalid input! No size limit will be applied.")
                max_file_size = None

        print(f"\n✅ READY TO EXPORT:\n   Chat: {name}\n   Media: {'yes' if download_media else 'no'}")
        if download_media and max_file_size is not None:
            print(f"   Max file size: {max_file_size} MB")
        confirm = input("\n▶️ Start export? [Y/n]: ").strip().lower()

        if confirm != 'n':
            exporter = ChatExporter(self.client, self.delay_settings)
            await exporter.export_chat(entity, download_media, max_file_size)
        else:
            print("❌ Export cancelled. Returning to main menu.")