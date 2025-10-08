import json
from pathlib import Path


class DelaySettings:
    def __init__(self):
        self.delay_between_messages = 0.3
        self.delay_between_media = 1.5
        self.max_retries = 5
        self.retry_delay = 3
        self.settings_file = Path("settings.json")
        self.load_settings()

    def load_settings(self):
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    self.delay_between_messages = data.get('delay_between_messages', 0.3)
                    self.delay_between_media = data.get('delay_between_media', 1.5)
                    self.max_retries = data.get('max_retries', 5)
                    self.retry_delay = data.get('retry_delay', 3)
            except:
                pass

    def save_settings(self):
        data = {
            'delay_between_messages': self.delay_between_messages,
            'delay_between_media': self.delay_between_media,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay
        }
        with open(self.settings_file, 'w') as f:
            json.dump(data, f, indent=2)

    def configure(self):
        print("\n⚙️ SETTINGS")
        print("=" * 60)
        print(f"Current settings:")
        print(f"  1. Delay between messages: {self.delay_between_messages}s")
        print(f"  2. Delay between media downloads: {self.delay_between_media}s")
        print(f"  3. Max retries on error: {self.max_retries}")
        print(f"  4. Retry delay: {self.retry_delay}s")
        print("\n💡 Recommendations:")
        print("  - For safe export: 0.5s+ message delay, 2s+ media delay")
        print("  - For fast export: 0.2s message delay, 1s media delay (risky)")
        print("  - Higher values = safer but slower")
        print("\nPresets:")
        print("  [1] Safe (slow): 0.5s / 2.5s")
        print("  [2] Balanced (recommended): 0.3s / 1.5s")
        print("  [3] Fast (risky): 0.1s / 1s")
        print("  [4] Custom")
        print("  [b] Back")

        choice = input("\nChoose preset (1-5): ").strip()

        if choice == '1':
            self.delay_between_messages = 0.5
            self.delay_between_media = 2.5
            self.max_retries = 5
            self.retry_delay = 5
            print("✅ Applied: Safe preset")
        elif choice == '2':
            self.delay_between_messages = 0.3
            self.delay_between_media = 1.5
            self.max_retries = 5
            self.retry_delay = 3
            print("✅ Applied: Balanced preset")
        elif choice == '3':
            self.delay_between_messages = 0.1
            self.delay_between_media = 1.0
            self.max_retries = 3
            self.retry_delay = 2
            print("⚠️ Applied: Fast preset (risky!)")
        elif choice == '4':
            try:
                msg_delay = input(
                    f"\nDelay between messages (current: {self.delay_between_messages}s): ").strip().replace(',', '.')
                if msg_delay: self.delay_between_messages = float(msg_delay)

                media_delay = input(
                    f"Delay between media downloads (current: {self.delay_between_media}s): ").strip().replace(',', '.')
                if media_delay: self.delay_between_media = float(media_delay)

                max_retry = input(f"Max retries on error (current: {self.max_retries}): ").strip()
                if max_retry: self.max_retries = int(max_retry)

                retry_delay = input(f"Retry delay (current: {self.retry_delay}s): ").strip().replace(',', '.')
                if retry_delay: self.retry_delay = float(retry_delay)

                print("✅ Custom settings applied!")
            except ValueError:
                print("❌ Invalid input! Settings not changed.")
                return
        elif choice == 'b':
            return
        else:
            print("❌ Invalid choice!")
            return

        self.save_settings()
        print("💾 Settings saved!")