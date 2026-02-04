#!/usr/bin/env python3
"""
Setup Pyrogram Session for Portal API (aportalsmp)

aportalsmp uses Pyrogram, not Telethon, so we need a Pyrogram session.
This script creates the correct session format.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("PORTAL_API_ID") or os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("PORTAL_API_HASH") or os.getenv("TELEGRAM_API_HASH")

if not API_ID or not API_HASH:
    print("❌ ERROR: Missing API credentials!")
    print("\nPlease set these in your .env file:")
    print("PORTAL_API_ID=your_api_id")
    print("PORTAL_API_HASH=your_api_hash")
    sys.exit(1)

try:
    from pyrogram import Client
except ImportError:
    print("❌ ERROR: pyrogram not installed!")
    print("\nInstall it with:")
    print("pip install pyrogram")
    sys.exit(1)

async def main():
    print("=" * 60)
    print("🔐 Pyrogram Session Setup for Portal API")
    print("=" * 60)
    print()
    print("This will create a Pyrogram session for aportalsmp.")
    print()
    print("You'll need to:")
    print("  1. Enter your phone number (with country code, e.g., +1234567890)")
    print("  2. Enter the code sent to your Telegram app")
    print("  3. If you have 2FA, enter your password")
    print()
    print("=" * 60)
    print()
    
    # Delete old incompatible session file
    if os.path.exists("account.session"):
        print("🗑️  Removing old Telethon session file...")
        os.remove("account.session")
    
    # Create Pyrogram client
    app = Client(
        "account",
        api_id=int(API_ID),
        api_hash=API_HASH,
        workdir="."
    )
    
    try:
        # Start the client (this will prompt for phone, code, etc.)
        await app.start()
        
        # Get session string
        session_string = await app.export_session_string()
        
        # Save to file
        with open('portal_session_string.txt', 'w') as f:
            f.write(session_string)
        
        # Stop the client
        await app.stop()
        
        print()
        print("=" * 60)
        print("✅ SUCCESS! Pyrogram session created!")
        print("=" * 60)
        print()
        print("Created files:")
        print("  ✓ account.session (Pyrogram format)")
        print("  ✓ portal_session_string.txt (updated)")
        print()
        print("⚠️  IMPORTANT:")
        print("  • Keep these files SECRET")
        print("  • They give access to your Telegram account")
        print("  • Already in .gitignore")
        print()
        print("🚀 Now test Portal API:")
        print("  python3 test_portal_live.py")
        print()
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ ERROR: {e}")
        print("=" * 60)
        print()
        print("Common issues:")
        print("  • Wrong phone number format (use +countrycode)")
        print("  • Wrong verification code")
        print("  • Wrong 2FA password")
        print("  • API credentials are invalid")
        print()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
