
import asyncio
import logging
import urllib.parse
import sys
import os
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MRKT_BOT_USERNAME = 'main_mrkt_bot'
MRKT_API_BASE = 'https://api.tgmrkt.io'

# Credentials
API_ID = 22307634
API_HASH = "7ab906fc6d065a2047a84411c1697593"
SESSION_NAME = "account"

try:
    from pyrogram import Client
    from pyrogram.raw.functions.messages import RequestWebView
    from pyrogram.raw.types import InputUser, InputPeerUser
except ImportError:
    logger.error("Pyrogram not installed? pip install pyrogram tgcrypto")
    sys.exit(1)

async def main():
    workdir = os.getcwd()
    logger.info(f"Working directory: {workdir}")
    logger.info(f"Using Session Name: {SESSION_NAME}")
    
    app = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH, workdir=workdir)
    
    async with app:
        logger.info("Connected to Pyrogram!")
        
        # Get bot entity
        try:
            bot = await app.get_users(MRKT_BOT_USERNAME)
            logger.info(f"Found bot: {bot.first_name} ({bot.id})")
        except Exception as e:
            logger.error(f"Failed to find bot {MRKT_BOT_USERNAME}: {e}")
            return

        # Prepare peer
        peer = await app.resolve_peer(MRKT_BOT_USERNAME)
        
        # Request WebView
        logger.info("Requesting WebView...")
        try:
            # Note: Pyrogram RequestWebView defaults to android usually, matching platform helps
            # But the portal_api used 'ios'.
            
            # Using raw function
            web_view = await app.invoke(
                RequestWebView(
                    peer=peer,
                    bot=peer,
                    platform="ios",
                    from_bot_menu=False,
                    url=f"{MRKT_API_BASE}/api/v1/auth"
                )
            )
            
            auth_url = web_view.url
            # logger.info(f"Got URL: {auth_url}")
            
            # Extract initData
            parsed = urllib.parse.urlparse(auth_url)
            fragment = parsed.fragment
            
            init_data = None
            if fragment and 'tgWebAppData=' in fragment:
                # Extract starting from tgWebAppData= until the next data block 
                # usually it's encoded.
                # Example: tgWebAppData=query_id%3D...&tgWebAppVersion=...
                # We need the VALUE of tgWebAppData.
                 
                # Let's split correctly
                parts = fragment.split('&')
                for part in parts:
                    if part.startswith('tgWebAppData='):
                        init_data_encoded = part.split('=', 1)[1]
                        init_data = urllib.parse.unquote(init_data_encoded)
                        break
            
            if not init_data:
                # Try query params
                qs = urllib.parse.parse_qs(parsed.query)
                if 'tgWebAppData' in qs:
                    init_data = qs['tgWebAppData'][0]

            if init_data:
                logger.info("✅ Extracted initData. Exchanging for Token...")
                
                # Exchange for JWT
                resp = requests.post(
                    f"{MRKT_API_BASE}/api/v1/auth",
                    json={'data': init_data},
                    headers={'Content-Type': 'application/json'}
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    token = data.get('accessToken') or data.get('token')
                    if token:
                        print(f"\nSUCCESS! NEW TOKEN:\n{token}\n")
                        with open("mrkt_token.txt", "w") as f:
                            f.write(token)
                    else:
                        logger.error("Token key missing in response")
                else:
                    logger.error(f"Auth failed HTTP {resp.status_code}: {resp.text}")
            else:
                logger.error("Could not parse tgWebAppData from URL")
                
        except Exception as e:
            logger.error(f"Error requesting webview: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
