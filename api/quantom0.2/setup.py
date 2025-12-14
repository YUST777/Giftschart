#!/usr/bin/env python3
"""Setup Telegram session for Quant Marketplace API access"""

import asyncio
from telethon import TelegramClient
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION_NAME


async def setup():
    """Setup and authorize Telegram session"""
    
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        print("❌ Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env")
        print("\n📝 Get credentials from: https://my.telegram.org/apps")
        return
    
    print("🔧 Setting up Telegram session...")
    print(f"📁 Session file: {TELEGRAM_SESSION_NAME}.session\n")
    
    client = TelegramClient(
        TELEGRAM_SESSION_NAME,
        int(TELEGRAM_API_ID),
        TELEGRAM_API_HASH
    )
    
    await client.start()
    
    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"✅ Session authorized!")
        print(f"👤 User: {me.first_name}")
        print(f"🆔 ID: {me.id}\n")
        print("✅ Ready to use Quant API!")
    else:
        print("❌ Authorization failed")
    
    await client.disconnect()


if __name__ == '__main__':
    asyncio.run(setup())
