import asyncio
import traceback
import logging
from core.ui import AppUI

logging.getLogger('telethon').setLevel(logging.ERROR)


async def main():
    app = AppUI()
    try:
        await app.start()
    except KeyboardInterrupt:
        print("\n\n👋 Program interrupted by user")
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())