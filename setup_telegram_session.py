#!/usr/bin/env python3
"""
Setup Telegram session for MRKT/Quant API authentication
"""
import os
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_SESSION_NAME = os.getenv('TELEGRAM_SESSION_NAME', 'mrkt_session')

async def setup_session():
    """Setup and authorize Telegram session"""
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        print("ERROR: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file")
        return False
    
    print(f"Connecting to Telegram with API ID: {TELEGRAM_API_ID}")
    print(f"Session name: {TELEGRAM_SESSION_NAME}")
    
    client = TelegramClient(TELEGRAM_SESSION_NAME, int(TELEGRAM_API_ID), TELEGRAM_API_HASH)
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            print("\n=== Telegram Authorization Required ===")
            print("Please enter your phone number (with country code, e.g., +1234567890):")
            phone = input("Phone: ")
            
            await client.send_code_request(phone)
            print("\nEnter the code you received:")
            code = input("Code: ")
            
            try:
                await client.sign_in(phone, code)
                print("✅ Successfully authorized!")
            except Exception as e:
                if "password" in str(e).lower():
                    print("\nTwo-factor authentication is enabled.")
                    print("Please enter your 2FA password:")
                    password = input("Password: ")
                    await client.sign_in(password=password)
                    print("✅ Successfully authorized with 2FA!")
                else:
                    raise
        
        # Test the connection
        me = await client.get_me()
        print(f"\n✅ Session setup complete!")
        print(f"Logged in as: {me.first_name} {me.last_name or ''} (@{me.username or 'no username'})")
        print(f"Phone: {me.phone}")
        
        await client.disconnect()
        return True
        
    except Exception as e:
        print(f"\n❌ Error setting up session: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(setup_session())
    if success:
        print("\n✅ Telegram session is ready for MRKT/Quant API!")
    else:
        print("\n❌ Failed to setup Telegram session")

