#!/usr/bin/env python3
"""
Generate Portal API Session String

This script helps generate a session string for Portal API authentication.
Run this interactively to create a session string that can be used in non-interactive environments.

Usage: python3 generate_session_string.py
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def generate_session_string():
    """Generate and save a session string for Portal API."""
    try:
        from pyrogram import Client
        
        API_ID = os.getenv("PORTAL_API_ID", "")
        API_HASH = os.getenv("PORTAL_API_HASH", "")
        
        if not API_ID or not API_HASH:
            print("❌ ERROR: PORTAL_API_ID and PORTAL_API_HASH must be set in .env file")
            return False
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        session_file = os.path.join(script_dir, "portal_session_string.txt")

        
        print("🔐 Portal API Session String Generator")
        print("=" * 50)
        print("\nThis will authenticate with Telegram and generate a session string.")
        print("You'll need to provide your phone number and verification code.\n")
        
        # Try to use existing session file first
        client = Client(
            "account",
            api_id=API_ID,
            api_hash=API_HASH,
            workdir=script_dir
        )
        
        await client.start()
        
        if client.is_connected:
            print("✅ Successfully connected using existing session!")
            session_string = await client.export_session_string()
            
            # Save session string
            with open(session_file, 'w') as f:
                f.write(session_string)
            
            print(f"✅ Session string generated and saved to: {session_file}")
            print(f"📏 Session string length: {len(session_string)} characters")
            print("\n💡 This session string can now be used for Portal API authentication")
            print("   in non-interactive environments.")
            
            await client.stop()
            return True
        else:
            print("❌ Failed to connect")
            await client.stop()
            return False
            
    except Exception as e:
        print(f"❌ Error generating session string: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(generate_session_string())
    sys.exit(0 if success else 1)
