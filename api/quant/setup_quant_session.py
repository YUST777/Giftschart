#!/usr/bin/env python3
"""Setup Telethon session for Quant Marketplace bot"""

import os
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_SESSION_NAME = os.getenv('TELEGRAM_SESSION_NAME', 'gifts_session')

async def setup_session():
    """Setup Telethon session"""
    
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        print("❌ Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file")
        return
    
    print("🔧 Setting up Telethon session for Quant Marketplace bot...")
    print(f"📁 Session file: {TELEGRAM_SESSION_NAME}.session")
    print()
    
    client = TelegramClient(TELEGRAM_SESSION_NAME, int(TELEGRAM_API_ID), TELEGRAM_API_HASH)
    
    await client.start()
    
    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"✅ Session created successfully!")
        print(f"👤 Logged in as: {me.first_name} (@{me.username if me.username else 'no username'})")
        print(f"🆔 User ID: {me.id}")
        print()
        print("✅ You can now run the Quant API tests!")
    else:
        print("❌ Authorization failed")
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(setup_session())
