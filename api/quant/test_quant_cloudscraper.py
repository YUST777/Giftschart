#!/usr/bin/env python3
"""Test Quant Marketplace using cloudscraper to bypass Cloudflare"""

import os
import asyncio
import json
import cloudscraper
import urllib.parse
from dotenv import load_dotenv
from telethon import TelegramClient, functions

load_dotenv()

BOT_USERNAME = 'QuantMarketRobot'
API_BASE = 'https://quant-marketplace.com'

TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_SESSION_NAME = os.getenv('TELEGRAM_SESSION_NAME', 'mrkt_session')

async def get_quant_init_data():
    """Get initData from Quant Marketplace bot"""
    
    client = None
    try:
        client = TelegramClient(TELEGRAM_SESSION_NAME, int(TELEGRAM_API_ID), TELEGRAM_API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            return None
        
        print("✅ Connected to Telegram")
        bot = await client.get_entity(BOT_USERNAME)
        
        result = await client(functions.messages.RequestWebViewRequest(
            peer=bot,
            bot=bot,
            platform="ios",
            url=API_BASE,
        ))
        
        if not result or not hasattr(result, 'url'):
            return None
        
        webview_url = result.url
        print(f"✅ Got WebView URL")
        
        parsed = urllib.parse.urlparse(webview_url)
        fragment = parsed.fragment
        
        if fragment and 'tgWebAppData=' in fragment:
            init_data_encoded = fragment.split('tgWebAppData=')[1]
            if '&' in init_data_encoded:
                init_data_encoded = init_data_encoded.split('&')[0]
            init_data = urllib.parse.unquote(init_data_encoded)
            return init_data
        
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        if client:
            await client.disconnect()

def test_with_cloudscraper(init_data):
    """Test API using cloudscraper"""
    
    print("\n🔥 Testing with cloudscraper (Cloudflare bypass)...\n")
    
    # Create scraper
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'ios',
            'mobile': True,
        }
    )
    
    # Test endpoints
    endpoints = [
        '/api/gifts',
        '/api/v1/gifts', 
        '/api/channels',
        '/api/me',
    ]
    
    for endpoint in endpoints:
        url = f"{API_BASE}{endpoint}"
        print(f"Testing: {endpoint}")
        
        # Try different auth methods
        auth_variants = [
            {},
            {'Authorization': init_data},
            {'Authorization': f'Bearer {init_data}'},
            {'Authorization': f'tma {init_data}'},
            {'x-telegram-init-data': init_data},
            {'x-init-data': init_data},
            {'tg-init-data': init_data},
        ]
        
        for headers in auth_variants:
            try:
                # Add common headers
                headers.update({
                    'Accept': 'application/json',
                    'Origin': API_BASE,
                    'Referer': f'{API_BASE}/',
                })
                
                response = scraper.get(url, headers=headers, timeout=20)
                
                if response.status_code == 200:
                    auth_type = [k for k in headers.keys() if 'auth' in k.lower() or 'init' in k.lower()]
                    auth_type = auth_type[0] if auth_type else "No auth"
                    
                    print(f"  ✅ SUCCESS! Auth method: {auth_type}")
                    print(f"     Status: {response.status_code}")
                    print(f"     Content length: {len(response.text)}")
                    
                    # Try to parse JSON
                    try:
                        data = response.json()
                        print(f"     ✅ Valid JSON response")
                        
                        # Save to file
                        filename = f"quant{endpoint.replace('/', '_')}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        print(f"     ✅ Saved to {filename}")
                        
                        # Show preview
                        preview = json.dumps(data, indent=2)[:500]
                        print(f"\n     Preview:\n{preview}...\n")
                        
                    except:
                        print(f"     ⚠️ Not JSON, raw text:")
                        print(f"     {response.text[:300]}")
                    
                    return True
                    
                elif response.status_code == 401:
                    print(f"  ⚠️ 401 Unauthorized")
                elif response.status_code == 403:
                    if 'cloudflare' not in response.text.lower():
                        print(f"  ⚠️ 403 Forbidden (auth issue)")
                elif response.status_code != 404:
                    print(f"  ⚠️ Status {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                if 'timeout' not in str(e).lower():
                    print(f"  ⚠️ Error: {e}")
        
        print()
    
    return False

async def main():
    """Main function"""
    
    print("🚀 Quant Marketplace API Access (with Cloudflare bypass)\n")
    print("=" * 80 + "\n")
    
    # Get initData
    print("📱 Step 1: Getting initData from Telegram bot...\n")
    init_data = await get_quant_init_data()
    
    if not init_data:
        print("❌ Could not get initData")
        return
    
    print(f"✅ Got initData (length: {len(init_data)})")
    print(f"   Preview: {init_data[:80]}...")
    
    print("\n" + "=" * 80)
    
    # Test API
    success = test_with_cloudscraper(init_data)
    
    if not success:
        print("\n❌ Could not access API endpoints")
        print("\n💡 Suggestions:")
        print("   1. The API might require a different authentication method")
        print("   2. Open the bot in Telegram and use DevTools to inspect requests")
        print("   3. Check if there's a session/cookie requirement")
        print("   4. The endpoints might be different from standard patterns")

if __name__ == '__main__':
    asyncio.run(main())
