#!/usr/bin/env python3
"""Download gifts collections JSON from TGMRKT API"""

import asyncio
import json
from dotenv import load_dotenv
from mrkt_bot import get_fresh_init_data, get_jwt_token, get_gifts_collections

load_dotenv()

async def download_json():
    """Download and save gifts collections JSON"""
    print("🔄 Fetching gifts collections from TGMRKT API...\n")
    
    # Step 1: Generate initData
    print("1️⃣ Generating initData...")
    init_data = await get_fresh_init_data()
    
    if not init_data:
        print("❌ Failed to generate initData")
        return
    
    print(f"✅ Generated initData")
    
    # Step 2: Get JWT token
    print(f"\n2️⃣ Authenticating...")
    jwt_token = get_jwt_token(init_data)
    
    if not jwt_token:
        print(f"❌ Authentication failed")
        return
    
    print(f"✅ Authenticated")
    
    # Step 3: Fetch collections
    print(f"\n3️⃣ Fetching collections data...")
    collections_data = get_gifts_collections()
    
    if not collections_data:
        print(f"❌ Failed to fetch collections")
        return
    
    print(f"✅ Successfully fetched collections!")
    
    # Step 4: Save to file
    output_file = "gifts_collections.json"
    print(f"\n4️⃣ Saving to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(collections_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved to {output_file}")
    print(f"\n🎉 SUCCESS! JSON file downloaded successfully!")
    
    # Print some stats
    if isinstance(collections_data, list):
        print(f"\n📊 Total items: {len(collections_data)}")
    elif isinstance(collections_data, dict):
        print(f"\n📊 Keys in data: {list(collections_data.keys())}")

if __name__ == '__main__':
    asyncio.run(download_json())
