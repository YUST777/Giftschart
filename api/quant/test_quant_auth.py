#!/usr/bin/env python3
"""Test Quant Marketplace authentication and API access"""

import os
import asyncio
import requests
import urllib.parse
from dotenv import load_dotenv
from telethon import TelegramClient, functions

load_dotenv()

# Quant Marketplace bot details
BOT_USERNAME = 'QuantMarketRobot'
BOT_ID = 7970333721
API_BASE = 'https://quant-marketplace.com'

TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_SESSION_NAME = os.getenv('TELEGRAM_SESSION_NAME', 'mrkt_session')

async def get_quant_init_data():
    """Get initData from Quant Marketplace bot"""
    
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        print("❌ TELEGRAM_API_ID and TELEGRAM_API_HASH must be set")
        return None
    
    client = None
    try:
        client = TelegramClient(TELEGRAM_SESSION_NAME, int(TELEGRAM_API_ID), TELEGRAM_API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            print("❌ Telethon session not authorized")
            return None
        
        print(f"✅ Connected to Telegram")
        
        # Get initData from Quant bot
        print(f"🔧 Getting initData from @{BOT_USERNAME}...")
        
        try:
            bot = await client.get_entity(BOT_USERNAME)
            
            # Request WebView
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
            print(f"✅ WebView URL obtained")
            print(f"   URL: {webview_url[:150]}...")
            
            # Parse initData from URL
            parsed = urllib.parse.urlparse(webview_url)
            
            # Check query params
            query_params = urllib.parse.parse_qs(parsed.query)
            if 'tgWebAppData' in query_params:
                init_data = urllib.parse.unquote(query_params['tgWebAppData'][0])
                print(f"✅ initData extracted from query (length: {len(init_data)})")
                return init_data
            
            # Check fragment
            fragment = parsed.fragment
            if fragment and 'tgWebAppData=' in fragment:
                init_data_encoded = fragment.split('tgWebAppData=')[1]
                if '&' in init_data_encoded:
                    init_data_encoded = init_data_encoded.split('&')[0]
                init_data = urllib.parse.unquote(init_data_encoded)
                print(f"✅ initData extracted from fragment (length: {len(init_data)})")
                return init_data
            
            print("⚠️ Could not find tgWebAppData in URL")
            print(f"   Full URL: {webview_url}")
            return None
            
        except Exception as e:
            print(f"❌ Error getting webview: {e}")
            return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        if client:
            await client.disconnect()

def test_auth_endpoints(init_data):
    """Test various authentication endpoint patterns"""
    
    print("\n🧪 Testing authentication endpoints...\n")
    
    # Common auth endpoint patterns
    auth_endpoints = [
        '/api/auth',
        '/api/v1/auth',
        '/api/login',
        '/api/user/auth',
        '/auth',
        '/auth/telegram',
        '/api/telegram/auth',
    ]
    
    results = []
    
    for endpoint in auth_endpoints:
        url = f"{API_BASE}{endpoint}"
        print(f"Testing: {url}")
        
        # Try different payload formats
        payloads = [
            {'data': init_data},
            {'initData': init_data},
            {'tgWebAppData': init_data},
            {'telegram_data': init_data},
        ]
        
        for i, payload in enumerate(payloads):
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                
                if response.status_code == 200:
                    print(f"  ✅ SUCCESS with payload format {i+1}!")
                    print(f"     Response: {response.text[:200]}")
                    results.append({
                        'endpoint': endpoint,
                        'payload': list(payload.keys())[0],
                        'response': response.json() if response.text else None
                    })
                    return results
                elif response.status_code != 404:
                    print(f"  ⚠️ Status {response.status_code}: {response.text[:100]}")
                    
            except requests.exceptions.Timeout:
                print(f"  ⏱️ Timeout")
            except Exception as e:
                pass
        
        print()
    
    return results

def test_gifts_endpoint_direct(init_data=None):
    """Try accessing /api/gifts directly with different auth methods"""
    
    print("\n🎁 Testing /api/gifts endpoint...\n")
    
    url = f"{API_BASE}/api/gifts"
    
    # Test 1: No auth
    print("1️⃣ Testing without authentication...")
    try:
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ SUCCESS! No auth needed!")
            print(f"   Response preview: {response.text[:300]}")
            return response.json()
        else:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    if not init_data:
        return None
    
    # Test 2: initData in headers
    print("\n2️⃣ Testing with initData in headers...")
    headers_variants = [
        {'Authorization': init_data},
        {'Authorization': f'Bearer {init_data}'},
        {'Authorization': f'tma {init_data}'},
        {'X-Telegram-Init-Data': init_data},
        {'X-Init-Data': init_data},
        {'tg-init-data': init_data},
    ]
    
    for headers in headers_variants:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"   ✅ SUCCESS with headers: {list(headers.keys())}")
                print(f"   Response preview: {response.text[:300]}")
                return response.json()
        except:
            pass
    
    print("   ❌ No success with header auth")
    
    # Test 3: initData in query params
    print("\n3️⃣ Testing with initData in query params...")
    param_variants = [
        {'initData': init_data},
        {'data': init_data},
        {'tgWebAppData': init_data},
    ]
    
    for params in param_variants:
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                print(f"   ✅ SUCCESS with params: {list(params.keys())}")
                print(f"   Response preview: {response.text[:300]}")
                return response.json()
        except:
            pass
    
    print("   ❌ No success with query params")
    
    return None

async def main():
    """Main test function"""
    
    print("🚀 Testing Quant Marketplace API Access\n")
    print("=" * 80)
    
    # Step 1: Get initData
    print("\n📱 Step 1: Getting initData from Telegram bot...\n")
    init_data = await get_quant_init_data()
    
    if init_data:
        print(f"\n✅ Got initData (length: {len(init_data)})")
        print(f"   Preview: {init_data[:100]}...")
    else:
        print("\n⚠️ Could not get initData, will try without auth")
    
    # Step 2: Test gifts endpoint directly
    gifts_data = test_gifts_endpoint_direct(init_data)
    
    if gifts_data:
        print("\n🎉 SUCCESS! Got gifts data!")
        import json
        with open('quant_gifts.json', 'w', encoding='utf-8') as f:
            json.dump(gifts_data, f, indent=2, ensure_ascii=False)
        print("✅ Saved to quant_gifts.json")
        return
    
    # Step 3: Try to find auth endpoint
    if init_data:
        print("\n" + "=" * 80)
        auth_results = test_auth_endpoints(init_data)
        
        if auth_results:
            print("\n🎉 Found working auth endpoint!")
            for result in auth_results:
                print(f"   Endpoint: {result['endpoint']}")
                print(f"   Payload key: {result['payload']}")
                print(f"   Response: {result['response']}")
        else:
            print("\n❌ Could not find working auth endpoint")
    
    print("\n" + "=" * 80)
    print("\n📋 Summary:")
    print("   - Check if the API requires authentication")
    print("   - The bot might use a different auth mechanism")
    print("   - Try inspecting the web app's network requests")

if __name__ == '__main__':
    asyncio.run(main())
