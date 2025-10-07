import asyncio
import traceback
from core.ui import AppUI

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