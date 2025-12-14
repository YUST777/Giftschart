#!/usr/bin/env python3
"""
TGMRKT Portfolio Bot
A bot that gets portfolio values from tgmrkt.io
"""

import os
import re
import json
import requests
import logging
import asyncio
import urllib.parse
import hashlib
import hmac
import time
import random
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telethon import TelegramClient, functions
from telethon.tl.types import InputBotAppShortName, InputUser

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_BASE = 'https://api.tgmrkt.io'
BOT_USERNAME = 'main_mrkt_bot'  # TGMRKT's official bot
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_SESSION_NAME = os.getenv('TELEGRAM_SESSION_NAME', 'mrkt_session')

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global variables for auth
current_jwt_token = None
refresh_task = None  # Background task for auto-refresh

async def get_fresh_init_data() -> str:
    """Get fresh initData using Telethon - AUTOMATIC METHOD!"""
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        logger.error("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in environment")
        return None
    
    client = None
    try:
        client = TelegramClient(TELEGRAM_SESSION_NAME, int(TELEGRAM_API_ID), TELEGRAM_API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            logger.warning("Telethon session not authorized. Run 'python3 setup_mrkt_session.py'")
            return None
        
        logger.info("Telethon client started with user session")
        
        # Get initData from TGMRKT bot
        logger.info(f"🔧 Getting initData from @{BOT_USERNAME}...")
        
        try:
            bot = await client.get_entity(BOT_USERNAME)
            
            # Request WebView from TGMRKT bot
            result = await client(functions.messages.RequestWebViewRequest(
                peer=bot,
                bot=bot,
                platform="ios",
                url=f"{API_BASE}/api/v1/auth",
            ))
            
            if not result or not hasattr(result, 'url'):
                logger.error("No URL in webview result")
                return None
            
            webview_url = result.url
            logger.info(f"✅ WebView URL obtained: {webview_url[:100]}...")
            
            # Parse initData from URL
            parsed = urllib.parse.urlparse(webview_url)
            
            # Check query params first
            query_params = urllib.parse.parse_qs(parsed.query)
            if 'tgWebAppData' in query_params:
                init_data = urllib.parse.unquote(query_params['tgWebAppData'][0])
                logger.info(f"✅ initData extracted from query (length: {len(init_data)})")
                logger.info(f"   Format: {init_data[:50]}...")
                return init_data
            
            # Check fragment (this is where it usually is)
            fragment = parsed.fragment
            if fragment and 'tgWebAppData=' in fragment:
                init_data_encoded = fragment.split('tgWebAppData=')[1]
                if '&' in init_data_encoded:
                    init_data_encoded = init_data_encoded.split('&')[0]
                init_data = urllib.parse.unquote(init_data_encoded)
                logger.info(f"✅ initData extracted from fragment (length: {len(init_data)})")
                logger.info(f"   Format: {init_data[:50]}...")
                return init_data
            
            logger.error("Could not find tgWebAppData in URL")
            return None
            
        except Exception as e:
            logger.error(f"Error getting webview: {e}")
            return None
        
    except Exception as e:
        logger.error(f"Error getting fresh initData: {e}")
        return None
    finally:
        if client:
            await client.disconnect()
            logger.info("Telethon client disconnected")

def get_jwt_token(init_data: str) -> str:
    """Get JWT token from initData"""
    global current_jwt_token
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        # TGMRKT expects JSON payload with 'data' field
        payload = {
            'data': init_data
        }
        
        response = requests.post(f"{API_BASE}/api/v1/auth", headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # Check for token in response
            if 'token' in data:
                current_jwt_token = data['token']
                logger.info("✅ JWT token obtained successfully")
                return current_jwt_token
            elif 'accessToken' in data:
                current_jwt_token = data['accessToken']
                logger.info("✅ JWT token obtained successfully")
                return current_jwt_token
            else:
                logger.error(f"No token in response: {data}")
                return None
        
        logger.error(f"Auth failed: {response.status_code} - {response.text}")
        return None
        
    except Exception as e:
        logger.error(f"Auth error: {e}")
        return None

def get_gifts_collections(retry_with_refresh: bool = True) -> dict:
    """Get gifts collections from API, auto-refresh token if expired"""
    global current_jwt_token
    
    if not current_jwt_token:
        # Try to refresh initData and get new token
        if retry_with_refresh:
            logger.info("No JWT token, attempting to refresh initData...")
            try:
                # Check if we're in an async context
                try:
                    loop = asyncio.get_running_loop()
                    logger.warning("Event loop running - refresh will happen in background")
                except RuntimeError:
                    # No running loop - safe to use asyncio.run()
                    init_data = asyncio.run(get_fresh_init_data())
                    if init_data:
                        get_jwt_token(init_data)
            except Exception as e:
                logger.error(f"Failed to refresh initData: {e}")
        
        if not current_jwt_token:
            logger.error("No JWT token available - cannot fetch collections")
            return None
    
    try:
        headers = {
            'Authorization': f'Bearer {current_jwt_token}',
            'Accept': 'application/json',
        }
        
        # Access the gifts collections endpoint
        endpoint = f"{API_BASE}/api/v1/gifts/collections"
        
        response = requests.get(endpoint, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Got gifts collections data")
            return data
        
        # If unauthorized (401) or forbidden (403), token might be expired
        if response.status_code in [401, 403] and retry_with_refresh:
            logger.warning(f"Token expired (status {response.status_code}), refreshing...")
            # Clear token and try to refresh
            current_jwt_token = None
            try:
                init_data = asyncio.run(get_fresh_init_data())
                if init_data:
                    new_token = get_jwt_token(init_data)
                    if new_token:
                        # Retry the request once with new token
                        logger.info("Retrying collections request with refreshed token...")
                        headers['Authorization'] = f'Bearer {new_token}'
                        retry_response = requests.get(endpoint, headers=headers, timeout=15)
                        if retry_response.status_code == 200:
                            retry_data = retry_response.json()
                            logger.info("✅ Successfully refreshed token and got collections")
                            return retry_data
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
        
        logger.error(f"Collections request failed: {response.status_code} - {response.text}")
        return None
        
    except Exception as e:
        logger.error(f"Collections error: {e}")
        return None

def format_collections_message(collections_data: dict) -> str:
    """Format collections data into a nice message"""
    
    if not collections_data:
        return "❌ Could not get collections data"
    
    lines = []
    lines.append(f"🎁 TGMRKT Gift Collections")
    lines.append("")
    
    # Display the data
    lines.append("📋 Collections Data:")
    lines.append(json.dumps(collections_data, indent=2))
    
    return "\n".join(lines)

# Bot command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    welcome_text = (
        "👋 Welcome to TGMRKT Bot!\n\n"
        "🎁 Get gift collections from tgmrkt.io\n\n"
        "🔧 Commands:\n"
        "• /collections - Get gift collections\n\n"
        "✅ Auto-refresh: Bot automatically refreshes authentication!"
    )
    
    await update.message.reply_text(welcome_text)

async def collections_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /collections command"""
    
    # Send typing action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    try:
        # Get gifts collections (will auto-refresh token if needed)
        collections_data = get_gifts_collections()
        
        if not collections_data:
            await update.message.reply_text(
                "❌ Could not fetch collections\n\n"
                "🔧 The bot needs authentication to tgmrkt.io\n\n"
                "Run: python3 setup_mrkt_session.py\n"
                "to enable auto-refresh!"
            )
            return
        
        # Format and send message
        message = format_collections_message(collections_data)
        await update.message.reply_text(message)
        
        logger.info(f"Collections data sent")
        
    except Exception as e:
        logger.error(f"Collections command error: {e}")
        await update.message.reply_text(
            "❌ An error occurred while processing your request\n\n"
            "Please try again later"
        )

def setup_bot():
    """Setup and configure the bot"""
    
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        print("Please set your bot token in .env file")
        return None
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("collections", collections_command))
    
    return application

def main():
    """Main function"""
    
    print("🚀 Starting TGMRKT Portfolio Bot...")
    
    # Setup bot
    application = setup_bot()
    if not application:
        return
    
    # Get fresh initData using Telethon webview (auto-refresh)
    print("🔐 Getting fresh initData via Telethon webview...")
    init_data = None
    try:
        init_data = asyncio.run(get_fresh_init_data())
        if init_data and len(init_data) > 50:
            print(f"✅ Fresh initData obtained (length: {len(init_data)})")
        else:
            print("⚠️ Could not get valid initData via webview")
    except Exception as e:
        print(f"⚠️ Error getting fresh initData: {e}")
    
    # Get JWT token using fresh initData
    if init_data and len(init_data) > 50:
        print("🔐 Getting JWT token from fresh initData...")
        try:
            token = get_jwt_token(init_data)
            if token:
                print("✅ Authentication successful!")
                print(f"✅ JWT token: {token[:30]}...")
            else:
                print("❌ Authentication failed - initData may be invalid")
        except Exception as e:
            print(f"❌ Authentication error: {e}")
    else:
        print("⚠️ No valid initData - portfolio commands won't work")
        
        # Check for manual initData override
        manual_init = os.getenv('MANUAL_INIT_DATA_MRKT')
        if manual_init:
            print("🔧 Found MANUAL_INIT_DATA_MRKT in environment, using it...")
            token = get_jwt_token(manual_init)
            if token:
                print("✅ Authentication successful with manual initData!")
            else:
                print("❌ Manual initData is invalid or expired")
    
    print("✅ Bot is ready!")
    print("\n📱 Available commands:")
    print("• /start - Welcome message")
    print("• /collections - Get gift collections")
    
    # Run bot
    print("🟢 Starting bot polling...")
    
    async def refresh_token_periodically():
        """Background task: Refresh JWT token every 50 seconds"""
        global current_jwt_token
        while True:
            try:
                await asyncio.sleep(50)
                logger.info("🔄 Auto-refreshing JWT token...")
                
                init_data = await get_fresh_init_data()
                
                if init_data:
                    new_token = get_jwt_token(init_data)
                    if new_token:
                        logger.info("✅ JWT token auto-refreshed successfully!")
                        current_jwt_token = new_token
                    else:
                        logger.warning("⚠️ Auto-refresh failed - token might still be valid")
                else:
                    logger.warning("⚠️ Could not get fresh initData for auto-refresh")
            except Exception as e:
                logger.error(f"❌ Auto-refresh error: {e}")
                await asyncio.sleep(10)
    
    async def main_async():
        global refresh_task
        async with application:
            await application.start()
            await application.updater.start_polling(drop_pending_updates=True)
            print("✅ Bot is now running and polling for messages!")
            
            # Start auto-refresh task
            refresh_task = asyncio.create_task(refresh_token_periodically())
            print("✅ Auto-refresh task started (refreshing every 50 seconds)")
            
            # Keep it alive
            try:
                await asyncio.Event().wait()
            except:
                pass
            finally:
                if refresh_task:
                    refresh_task.cancel()
    
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Bot error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
