#!/usr/bin/env python3
"""Test script to verify TGMRKT authentication and API access"""

import asyncio
import os
from dotenv import load_dotenv
from mrkt_bot import get_fresh_init_data, get_jwt_token, get_gifts_collections

load_dotenv()

async def test_auth():
    """Test TGMRKT authentication and API access"""
    print("🧪 Testing TGMRKT authentication and API access...\n")
    
    # Step 1: Generate initData
    print("1️⃣ Generating initData...")
    init_data = await get_fresh_init_data()
    
    if not init_data:
        print("❌ Failed to generate initData")
        print("💡 Make sure you've run: python3 setup_mrkt_session.py")
        return
    
    print(f"✅ Generated initData (length: {len(init_data)})")
    print(f"   Preview: {init_data[:100]}...")
    
    # Step 2: Test authentication
    print(f"\n2️⃣ Testing authentication...")
    jwt_token = get_jwt_token(init_data)
    
    if not jwt_token:
        print(f"❌ Authentication failed")
        return
    
    print(f"✅ Authentication successful!")
    print(f"   JWT token: {jwt_token[:50]}...")
    
    # Step 3: Test API access
    print(f"\n3️⃣ Testing API access to /api/v1/gifts/collections...")
    collections_data = get_gifts_collections()
    
    if not collections_data:
        print(f"❌ Failed to fetch collections")
        return
    
    print(f"✅ Successfully fetched collections!")
    print(f"\n📋 Collections data:")
    import json
    print(json.dumps(collections_data, indent=2))
    
    print(f"\n🎉 SUCCESS! All tests passed!")

if __name__ == '__main__':
    asyncio.run(test_auth())
