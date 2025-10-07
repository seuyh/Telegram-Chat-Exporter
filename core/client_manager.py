from pathlib import Path
from typing import Optional
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError


class ClientManager:
    def __init__(self):
        self.sessions_folder = Path("sessions")
        self.sessions_folder.mkdir(exist_ok=True)
        self.client = None

    async def select_session(self) -> Optional[str]:
        session_files = list(self.sessions_folder.glob("*.session"))
        if not session_files:
            print("\n❌ No saved sessions! Create a new one.")
            return None

        print("\n📂 AVAILABLE SESSIONS:")
        for idx, file in enumerate(session_files, 1):
            print(f"{idx}. {file.stem}")
        print(f"{len(session_files) + 1}. ⬅️ Back")

        while True:
            try:
                choice = int(input(f"\nSelect session (1-{len(session_files) + 1}): ").strip())
                if choice == len(session_files) + 1: return None
                if 1 <= choice <= len(session_files):
                    session_file = session_files[choice - 1].stem
                    print(f"✅ Selected session: {session_file}")
                    return session_file
                else:
                    print(f"❌ Enter number from 1 to {len(session_files) + 1}")
            except (ValueError, IndexError):
                print("❌ Enter a valid number!")
            except KeyboardInterrupt:
                return None

    async def create_new_session(self):
        print("\n➕ CREATE NEW SESSION (get credentials at https://my.telegram.org)")
        try:
            api_id = input("API ID: ").strip()
            api_hash = input("API Hash: ").strip()
            phone = input("Phone number (with +): ").strip()
            session_name = input("Session name (e.g., my_account): ").strip()

            if not all([api_id, api_hash, phone, session_name]):
                print("❌ All fields are required!")
                return

            session_path = str(self.sessions_folder / session_name)
            client = TelegramClient(session_path, int(api_id), api_hash, system_version='4.16.30-vxCUSTOM')

            print("\n📱 Connecting...")
            await client.connect()

            if not await client.is_user_authorized():
                await client.send_code_request(phone)
                print("\n📨 Code sent to Telegram")
                try:
                    await client.sign_in(phone, input("Enter code: ").strip())
                except SessionPasswordNeededError:
                    await client.sign_in(password=input("Enter 2FA password: ").strip())

            me = await client.get_me()
            print(f"\n✅ Successfully authorized: {me.first_name}\n💾 Session saved: {session_name}.session")
            await client.disconnect()

        except ValueError:
            print("❌ API ID must be a number!")
        except Exception as e:
            print(f"❌ Authorization error: {e}")

    async def get_client(self, session_name: str) -> Optional[TelegramClient]:
        session_path = str(self.sessions_folder / session_name)
        self.client = TelegramClient(session_path, 12345, '0123456789abcdef0123456789abcdef')
        try:
            print("\n⏳ Connecting to existing session...")
            await self.client.connect()
            if not await self.client.is_user_authorized():
                print("❌ Session is not authorized or outdated.")
                await self.client.disconnect()
                return None
            me = await self.client.get_me()
            print(f"✅ Authorized: {me.first_name} (@{me.username or 'no username'})")
            return self.client
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return None