#!/usr/bin/env python3
"""Test /api/gifts/gifts endpoint using cloudscraper to bypass Cloudflare"""

import os
import asyncio
import json
import urllib.parse
from dotenv import load_dotenv
from telethon import TelegramClient, functions

try:
    import cloudscraper
except ImportError:
    print("❌ cloudscraper not installed. Installing...")
    import subprocess
    subprocess.check_call(['pip3', 'install', 'cloudscraper'])
    import cloudscraper

load_dotenv()

BOT_USERNAME = 'QuantMarketRobot'
API_BASE = 'https://quant-marketplace.com'
GIFTS_ENDPOINT = '/api/gifts/gifts'

TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_SESSION_NAME = os.getenv('TELEGRAM_SESSION_NAME', 'gifts_session')

async def get_quant_init_data():
    """Get initData from Quant Marketplace bot"""
    
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        print("❌ Missing TELEGRAM_API_ID or TELEGRAM_API_HASH")
        return None
    
    client = None
    try:
        client = TelegramClient(TELEGRAM_SESSION_NAME, int(TELEGRAM_API_ID), TELEGRAM_API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            print("❌ Session not authorized")
            return None
        
        print("✅ Connected to Telegram")
        
        try:
            bot = await client.get_entity(BOT_USERNAME)
        except Exception as e:
            print(f"❌ Could not find bot @{BOT_USERNAME}: {e}")
            return None
        
        result = await client(functions.messages.RequestWebViewRequest(
            peer=bot,
            bot=bot,
            platform="ios",
            url=API_BASE,
        ))
        
        if not result or not hasattr(result, 'url'):
            return None
        
        webview_url = result.url
        print("✅ Got WebView URL")
        
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
        
        return None
        
    except Exception as e:
        print(f"Error getting initData: {e}")
        return None
    finally:
        if client:
            await client.disconnect()

def test_with_cloudscraper(init_data=None):
    """Test the endpoint using cloudscraper"""
    
    url = f"{API_BASE}{GIFTS_ENDPOINT}"
    print(f"\n🔥 Testing with cloudscraper (Cloudflare bypass)\n")
    print(f"URL: {url}\n")
    print("=" * 80 + "\n")
    
    # Create scraper with mobile browser profile
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'ios',
            'mobile': True,
        }
    )
    
    # Test 1: No authentication
    print("1️⃣ Testing without authentication...")
    try:
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
            'Origin': API_BASE,
            'Referer': f'{API_BASE}/',
        }
        
        response = scraper.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS! No auth required!")
            print(f"   Status: {response.status_code}")
            print(f"   Content length: {len(response.text)}")
            
            try:
                data = response.json()
                print(f"   ✅ Valid JSON response")
                
                # Save to file
                with open('quant_gifts_gifts.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"   ✅ Saved to quant/quant_gifts_gifts.json")
                
                # Show summary
                if isinstance(data, list):
                    print(f"\n   📊 Response: List with {len(data)} items")
                    if data:
                        print(f"   First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'N/A'}")
                elif isinstance(data, dict):
                    print(f"\n   📊 Response: Dictionary")
                    print(f"   Keys: {list(data.keys())}")
                
                # Show preview
                preview = json.dumps(data, indent=2)[:500]
                print(f"\n   Preview:\n{preview}...\n")
                
                return data
                
            except json.JSONDecodeError:
                print(f"   ⚠️ Response is not JSON")
                print(f"   Response: {response.text[:300]}")
                
        else:
            print(f"   Status: {response.status_code}")
            if 'cloudflare' in response.text.lower() or 'just a moment' in response.text.lower():
                print(f"   ⚠️ Still blocked by Cloudflare")
            else:
                print(f"   Response: {response.text[:200]}")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    if not init_data:
        print("\n⚠️ No initData available, skipping authenticated tests")
        return None
    
    # Test 2: With authentication
    print("\n2️⃣ Testing with authentication headers...")
    
    auth_variants = [
        ('Bearer', {'Authorization': f'Bearer {init_data}'}),
        ('tma', {'Authorization': f'tma {init_data}'}),
        ('Raw', {'Authorization': init_data}),
        ('x-telegram-init-data', {'x-telegram-init-data': init_data}),
        ('x-init-data', {'x-init-data': init_data}),
    ]
    
    for name, auth_headers in auth_variants:
        try:
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
                'Origin': API_BASE,
                'Referer': f'{API_BASE}/',
            }
            headers.update(auth_headers)
            
            response = scraper.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS with {name}!")
                
                try:
                    data = response.json()
                    with open('quant_gifts_gifts.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"   ✅ Saved to quant/quant_gifts_gifts.json")
                    
                    if isinstance(data, list):
                        print(f"   📊 List with {len(data)} items")
                    elif isinstance(data, dict):
                        print(f"   📊 Dictionary with keys: {list(data.keys())}")
                    
                    return data
                    
                except:
                    print(f"   Response: {response.text[:200]}")
                    
            elif response.status_code == 401:
                print(f"   {name}: 401 Unauthorized")
            elif response.status_code == 403:
                if 'cloudflare' not in response.text.lower():
                    print(f"   {name}: 403 Forbidden")
                    
        except Exception as e:
            pass
    
    print("\n❌ All methods failed")
    return None

async def main():
    """Main function"""
    
    print("🚀 Testing Quant Marketplace /api/gifts/gifts (Cloudflare Bypass)\n")
    print("=" * 80 + "\n")
    
    # Try to get initData
    print("📱 Step 1: Getting initData from Telegram bot...\n")
    init_data = await get_quant_init_data()
    
    if init_data:
        print(f"✅ Got initData (length: {len(init_data)})")
        print(f"   Preview: {init_data[:100]}...\n")
    else:
        print("⚠️ Could not get initData, will try without authentication\n")
    
    print("=" * 80)
    
    # Test the endpoint
    result = test_with_cloudscraper(init_data)
    
    print("\n" + "=" * 80)
    
    if result:
        print("\n🎉 SUCCESS! Retrieved data from /api/gifts/gifts")
    else:
        print("\n❌ Could not access the endpoint")
        print("\n💡 Next steps:")
        print("   1. Open the Quant bot in Telegram")
        print("   2. Open browser DevTools (F12)")
        print("   3. Look at Network tab for API requests")
        print("   4. Check the actual headers and authentication used")

if __name__ == '__main__':
    asyncio.run(main())
