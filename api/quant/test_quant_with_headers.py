#!/usr/bin/env python3
"""Test Quant Marketplace with proper browser headers"""

import os
import asyncio
import requests
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
        parsed = urllib.parse.urlparse(webview_url)
        
        # Check fragment
        fragment = parsed.fragment
        if fragment and 'tgWebAppData=' in fragment:
            init_data_encoded = fragment.split('tgWebAppData=')[1]
            if '&' in init_data_encoded:
                init_data_encoded = init_data_encoded.split('&')[0]
            init_data = urllib.parse.unquote(init_data_encoded)
            return init_data
        
        return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        if client:
            await client.disconnect()

def get_browser_headers(init_data=None):
    """Get realistic browser headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Origin': 'https://quant-marketplace.com',
        'Referer': 'https://quant-marketplace.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }
    
    if init_data:
        # Try different auth header formats
        headers['Authorization'] = f'tma {init_data}'
    
    return headers

def test_api_endpoints(init_data):
    """Test API endpoints with proper headers"""
    
    print("🧪 Testing Quant Marketplace API\n")
    
    session = requests.Session()
    
    # Test different endpoints
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
        auth_methods = [
            {},  # No auth
            {'Authorization': init_data},
            {'Authorization': f'Bearer {init_data}'},
            {'Authorization': f'tma {init_data}'},
            {'x-telegram-init-data': init_data},
            {'x-init-data': init_data},
        ]
        
        for auth_headers in auth_methods:
            try:
                headers = get_browser_headers()
                headers.update(auth_headers)
                
                response = session.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    auth_type = list(auth_headers.keys())[0] if auth_headers else "No auth"
                    print(f"  ✅ SUCCESS! Auth: {auth_type}")
                    print(f"     Response length: {len(response.text)}")
                    print(f"     Preview: {response.text[:200]}")
                    
                    # Save response
                    import json
                    try:
                        data = response.json()
                        filename = f"quant_{endpoint.replace('/', '_')}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        print(f"     ✅ Saved to {filename}")
                    except:
                        pass
                    
                    return True
                    
                elif response.status_code == 403:
                    # Cloudflare block
                    if 'cloudflare' in response.text.lower() or 'just a moment' in response.text.lower():
                        continue
                    else:
                        print(f"  ⚠️ 403 Forbidden (not Cloudflare)")
                        
                elif response.status_code == 401:
                    print(f"  ⚠️ 401 Unauthorized")
                    
                elif response.status_code != 404:
                    print(f"  ⚠️ Status {response.status_code}")
                    
            except Exception as e:
                pass
        
        print()
    
    return False

async def main():
    """Main function"""
    
    print("🚀 Quant Marketplace API Test\n")
    print("=" * 80 + "\n")
    
    # Get initData
    print("📱 Getting initData from Telegram...\n")
    init_data = await get_quant_init_data()
    
    if not init_data:
        print("❌ Could not get initData")
        return
    
    print(f"✅ Got initData (length: {len(init_data)})")
    print(f"   Preview: {init_data[:80]}...\n")
    
    print("=" * 80 + "\n")
    
    # Test API
    success = test_api_endpoints(init_data)
    
    if not success:
        print("\n❌ Could not access API")
        print("\n💡 The API is protected by Cloudflare")
        print("   You may need to:")
        print("   1. Access the web app directly in Telegram")
        print("   2. Use browser DevTools to inspect network requests")
        print("   3. Copy the actual request headers and cookies")
        print("   4. Use a tool like cloudscraper or selenium")

if __name__ == '__main__':
    asyncio.run(main())
