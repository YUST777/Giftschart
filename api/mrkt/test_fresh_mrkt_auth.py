#!/usr/bin/env python3
"""
Test script to generate FRESH authentication from scratch
This will create new initData and test if it works
"""

import asyncio
import os
import json
import requests
from dotenv import load_dotenv
from telethon import TelegramClient, functions

load_dotenv()

TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
BOT_USERNAME = 'main_mrkt_bot'
API_BASE = 'https://api.tgmrkt.io'

async def generate_fresh_auth():
    """Generate completely fresh authentication"""
    
    print("🔧 Generating FRESH authentication from scratch...")
    print(f"   Target bot: @{BOT_USERNAME}")
    print(f"   API: {API_BASE}")
    print()
    
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        print("❌ TELEGRAM_API_ID and TELEGRAM_API_HASH required in .env")
        return
    
    # Use existing session to generate fresh initData
    session_name = os.getenv('TELEGRAM_SESSION_NAME', 'gifts_session')
    client = TelegramClient(session_name, int(TELEGRAM_API_ID), TELEGRAM_API_HASH)
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            print("❌ Not authorized. Run: python3 setup_mrkt_session.py")
            return
        
        me = await client.get_me()
        print(f"✅ Connected as: {me.first_name} (@{me.username})")
        print(f"   User ID: {me.id}")
        print()
        
        # Step 1: Get fresh initData from WebView
        print("1️⃣ Requesting WebView from @main_mrkt_bot...")
        
        bot = await client.get_entity(BOT_USERNAME)
        
        result = await client(functions.messages.RequestWebViewRequest(
            peer=bot,
            bot=bot,
            platform="ios",
            url=f"{API_BASE}/api/v1/auth",
        ))
        
        if not result or not hasattr(result, 'url'):
            print("❌ No URL in webview result")
            return
        
        webview_url = result.url
        print(f"✅ Got WebView URL")
        print(f"   Length: {len(webview_url)} chars")
        
        # Step 2: Extract initData from URL
        print("\n2️⃣ Extracting initData from WebView URL...")
        
        import urllib.parse
        parsed = urllib.parse.urlparse(webview_url)
        
        init_data = None
        
        # Check query params
        query_params = urllib.parse.parse_qs(parsed.query)
        if 'tgWebAppData' in query_params:
            init_data = urllib.parse.unquote(query_params['tgWebAppData'][0])
        
        # Check fragment
        if not init_data:
            fragment = parsed.fragment
            if fragment and 'tgWebAppData=' in fragment:
                init_data_encoded = fragment.split('tgWebAppData=')[1]
                if '&' in init_data_encoded:
                    init_data_encoded = init_data_encoded.split('&')[0]
                init_data = urllib.parse.unquote(init_data_encoded)
        
        if not init_data:
            print("❌ Could not extract initData from URL")
            return
        
        print(f"✅ Extracted initData")
        print(f"   Length: {len(init_data)} chars")
        print(f"   Preview: {init_data[:100]}...")
        
        # Step 3: Exchange initData for JWT token
        print("\n3️⃣ Exchanging initData for JWT token...")
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        payload = {
            'data': init_data
        }
        
        response = requests.post(f"{API_BASE}/api/v1/auth", headers=headers, json=payload, timeout=15)
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Authentication failed")
            print(f"   Response: {response.text}")
            return
        
        data = response.json()
        
        # Try to find token in response
        jwt_token = None
        if 'token' in data:
            jwt_token = data['token']
        elif 'accessToken' in data:
            jwt_token = data['accessToken']
        elif 'data' in data and isinstance(data['data'], str):
            jwt_token = data['data']
        
        if not jwt_token:
            print(f"❌ No token in response")
            print(f"   Response: {json.dumps(data, indent=2)}")
            return
        
        print(f"✅ Got JWT token!")
        print(f"   Token: {jwt_token[:50]}...")
        
        # Step 4: Test API access with the token
        print("\n4️⃣ Testing API access to /api/v1/gifts/collections...")
        
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Accept': 'application/json',
        }
        
        response = requests.get(f"{API_BASE}/api/v1/gifts/collections", headers=headers, timeout=15)
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API access failed")
            print(f"   Response: {response.text}")
            return
        
        collections_data = response.json()
        
        print(f"✅ Successfully accessed API!")
        
        # Show summary
        if isinstance(collections_data, list):
            print(f"\n📊 Collections Summary:")
            print(f"   Total items: {len(collections_data)}")
            if len(collections_data) > 0:
                print(f"\n   First 5 items:")
                for i, item in enumerate(collections_data[:5]):
                    name = item.get('name', 'Unknown')
                    title = item.get('title', 'Unknown')
                    floor_price = item.get('floorPriceNanoTons', 0)
                    print(f"   {i+1}. {title} - Floor: {floor_price/1e9:.2f} TON")
        else:
            print(f"\n📋 Response data:")
            print(json.dumps(collections_data, indent=2)[:500])
        
        print(f"\n🎉 SUCCESS! Fresh authentication works perfectly!")
        print(f"\n✅ Summary:")
        print(f"   1. Generated fresh initData from @{BOT_USERNAME}")
        print(f"   2. Exchanged for JWT token")
        print(f"   3. Successfully accessed API")
        print(f"   4. Retrieved {len(collections_data) if isinstance(collections_data, list) else 'N/A'} collections")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.disconnect()
        print("\n✅ Disconnected")

if __name__ == '__main__':
    asyncio.run(generate_fresh_auth())
