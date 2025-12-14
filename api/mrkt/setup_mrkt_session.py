#!/usr/bin/env python3
"""
Setup Telethon session for TGMRKT bot
Run this once to create a session file for automatic authentication
"""

import os
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_SESSION_NAME = os.getenv('TELEGRAM_SESSION_NAME', 'mrkt_session')

async def setup_session():
    """Setup Telethon session"""
    
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        print("❌ Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file")
        print("\n📝 To get these credentials:")
        print("1. Visit https://my.telegram.org/apps")
        print("2. Log in with your phone number")
        print("3. Create a new application")
        print("4. Copy API ID and API Hash to your .env file")
        return
    
    print("🔧 Setting up Telethon session for TGMRKT bot...")
    print(f"📁 Session file: {TELEGRAM_SESSION_NAME}.session")
    print()
    
    client = TelegramClient(TELEGRAM_SESSION_NAME, int(TELEGRAM_API_ID), TELEGRAM_API_HASH)
    
    await client.start()
    
    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"✅ Session created successfully!")
        print(f"👤 Logged in as: {me.first_name} (@{me.username})")
        print(f"🆔 User ID: {me.id}")
        print()
        print("✅ You can now run the bot with automatic authentication!")
        print("   python3 mrkt_bot.py")
    else:
        print("❌ Authorization failed")
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(setup_session())
