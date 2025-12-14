#!/usr/bin/env python3
"""Test the new Quant Marketplace /api/gifts/gifts endpoint"""

import os
import asyncio
import requests
import json
import urllib.parse
from dotenv import load_dotenv
from telethon import TelegramClient, functions

load_dotenv()

BOT_USERNAME = 'QuantMarketRobot'
API_BASE = 'https://quant-marketplace.com'
GIFTS_ENDPOINT = '/api/gifts/gifts'

TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_SESSION_NAME = os.getenv('TELEGRAM_SESSION_NAME', 'mrkt_session')

async def get_quant_init_data():
    """Get initData from Quant Marketplace bot"""
    
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        print("❌ TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env")
        return None
    
    client = None
    try:
        client = TelegramClient(TELEGRAM_SESSION_NAME, int(TELEGRAM_API_ID), TELEGRAM_API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            print("❌ Telethon session not authorized. Run setup script first.")
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
            print("❌ No URL in webview result")
            return None
        
        webview_url = result.url
        print(f"✅ Got WebView URL")
        
        parsed = urllib.parse.urlparse(webview_url)
        
        # Check query params
        query_params = urllib.parse.parse_qs(parsed.query)
        if 'tgWebAppData' in query_params:
            init_data = urllib.parse.unquote(query_params['tgWebAppData'][0])
            return init_data
        
        # Check fragment
        fragment = parsed.fragment
        if fragment and 'tgWebAppData=' in fragment:
            init_data_encoded = fragment.split('tgWebAppData=')[1]
            if '&' in init_data_encoded:
                init_data_encoded = init_data_encoded.split('&')[0]
            init_data = urllib.parse.unquote(init_data_encoded)
            return init_data
        
        print("⚠️ Could not find tgWebAppData in URL")
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        if client:
            await client.disconnect()

def test_gifts_endpoint(init_data=None):
    """Test the /api/gifts/gifts endpoint with various methods"""
    
    url = f"{API_BASE}{GIFTS_ENDPOINT}"
    print(f"\n🎁 Testing endpoint: {GIFTS_ENDPOINT}\n")
    print(f"Full URL: {url}\n")
    print("=" * 80 + "\n")
    
    # Test 1: No authentication
    print("1️⃣ Testing without authentication...")
    try:
        response = requests.get(url, timeout=15)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS! No auth required!")
            try:
                data = response.json()
                print(f"   Response type: {type(data)}")
                if isinstance(data, list):
                    print(f"   Items count: {len(data)}")
                elif isinstance(data, dict):
                    print(f"   Keys: {list(data.keys())}")
                
                # Save response
                with open('quant/quant_gifts_gifts.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"   ✅ Saved to quant/quant_gifts_gifts.json")
                
                # Show preview
                preview = json.dumps(data, indent=2)[:500]
                print(f"\n   Preview:\n{preview}...\n")
                
                return data
            except json.JSONDecodeError:
                print(f"   ⚠️ Response is not JSON")
                print(f"   Response: {response.text[:300]}")
        else:
            print(f"   Response: {response.text[:200]}")
    except requests.exceptions.Timeout:
        print(f"   ⏱️ Request timeout")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    if not init_data:
        print("\n⚠️ No initData available, skipping authenticated tests")
        return None
    
    # Test 2: With Authorization header (various formats)
    print("\n2️⃣ Testing with Authorization headers...")
    
    auth_formats = [
        ('Bearer', f'Bearer {init_data}'),
        ('tma', f'tma {init_data}'),
        ('Raw', init_data),
    ]
    
    for name, auth_value in auth_formats:
        try:
            headers = {
                'Authorization': auth_value,
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
                'Origin': API_BASE,
                'Referer': f'{API_BASE}/',
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS with {name} format!")
                data = response.json()
                
                with open('quant/quant_gifts_gifts.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"   ✅ Saved to quant/quant_gifts_gifts.json")
                
                return data
            elif response.status_code != 404:
                print(f"   {name}: Status {response.status_code}")
                
        except Exception as e:
            pass
    
    # Test 3: With custom headers
    print("\n3️⃣ Testing with custom init-data headers...")
    
    header_variants = [
        {'x-telegram-init-data': init_data},
        {'x-init-data': init_data},
        {'tg-init-data': init_data},
        {'telegram-data': init_data},
    ]
    
    for custom_headers in header_variants:
        try:
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
                'Origin': API_BASE,
                'Referer': f'{API_BASE}/',
            }
            headers.update(custom_headers)
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                header_name = list(custom_headers.keys())[0]
                print(f"   ✅ SUCCESS with {header_name} header!")
                data = response.json()
                
                with open('quant/quant_gifts_gifts.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"   ✅ Saved to quant/quant_gifts_gifts.json")
                
                return data
                
        except Exception as e:
            pass
    
    # Test 4: With query parameters
    print("\n4️⃣ Testing with query parameters...")
    
    param_variants = [
        {'initData': init_data},
        {'data': init_data},
        {'tgWebAppData': init_data},
    ]
    
    for params in param_variants:
        try:
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                param_name = list(params.keys())[0]
                print(f"   ✅ SUCCESS with {param_name} parameter!")
                data = response.json()
                
                with open('quant/quant_gifts_gifts.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"   ✅ Saved to quant/quant_gifts_gifts.json")
                
                return data
                
        except Exception as e:
            pass
    
    print("\n❌ All authentication methods failed")
    return None

async def main():
    """Main test function"""
    
    print("🚀 Testing Quant Marketplace /api/gifts/gifts Endpoint\n")
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
    result = test_gifts_endpoint(init_data)
    
    print("\n" + "=" * 80)
    
    if result:
        print("\n🎉 SUCCESS! Retrieved gifts data from /api/gifts/gifts")
        print(f"\n📊 Data summary:")
        if isinstance(result, list):
            print(f"   - Type: List")
            print(f"   - Count: {len(result)} items")
            if result:
                print(f"   - First item keys: {list(result[0].keys()) if isinstance(result[0], dict) else 'N/A'}")
        elif isinstance(result, dict):
            print(f"   - Type: Dictionary")
            print(f"   - Keys: {list(result.keys())}")
    else:
        print("\n❌ Could not access the endpoint")
        print("\n💡 Suggestions:")
        print("   1. Verify the endpoint URL is correct")
        print("   2. Check if Cloudflare protection is active")
        print("   3. Try accessing the web app in Telegram and inspect network requests")
        print("   4. The endpoint might require a different authentication method")

if __name__ == '__main__':
    asyncio.run(main())
