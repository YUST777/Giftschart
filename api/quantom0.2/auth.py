"""Authentication handler for Quant Marketplace"""

import urllib.parse
from telethon import TelegramClient, functions
from config import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_SESSION_NAME,
    BOT_USERNAME,
    API_BASE
)


async def get_init_data():
    """Get initData from Quant Marketplace bot via Telegram"""
    
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env")
    
    client = TelegramClient(
        TELEGRAM_SESSION_NAME,
        int(TELEGRAM_API_ID),
        TELEGRAM_API_HASH
    )
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            raise Exception("Session not authorized. Run setup.py first.")
        
        bot = await client.get_entity(BOT_USERNAME)
        
        result = await client(functions.messages.RequestWebViewRequest(
            peer=bot,
            bot=bot,
            platform="ios",
            url=API_BASE,
        ))
        
        if not result or not hasattr(result, 'url'):
            raise Exception("No URL in webview result")
        
        webview_url = result.url
        parsed = urllib.parse.urlparse(webview_url)
        
        # Check query params
        query_params = urllib.parse.parse_qs(parsed.query)
        if 'tgWebAppData' in query_params:
            return urllib.parse.unquote(query_params['tgWebAppData'][0])
        
        # Check fragment
        fragment = parsed.fragment
        if fragment and 'tgWebAppData=' in fragment:
            init_data_encoded = fragment.split('tgWebAppData=')[1]
            if '&' in init_data_encoded:
                init_data_encoded = init_data_encoded.split('&')[0]
            return urllib.parse.unquote(init_data_encoded)
        
        raise Exception("Could not find tgWebAppData in URL")
        
    finally:
        await client.disconnect()
