#!/usr/bin/env python3
"""Main script to fetch Quant Marketplace gifts data"""

import asyncio
import json
from auth import get_init_data
from api import QuantAPI


async def main():
    """Fetch and display gifts data"""
    
    print("🚀 Quant Marketplace API Client\n")
    
    # Get authentication
    print("🔐 Authenticating...")
    try:
        init_data = await get_init_data()
        print("✅ Authenticated\n")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("\n💡 Run setup.py first to authorize your session")
        return
    
    # Fetch gifts data
    print("📡 Fetching gifts data...")
    try:
        api = QuantAPI(init_data)
        data = api.get_gifts()
        print("✅ Data retrieved\n")
    except Exception as e:
        print(f"❌ API request failed: {e}")
        return
    
    # Display summary
    print("📊 Summary:")
    print(f"  Gifts: {len(data.get('gifts', []))}")
    print(f"  Backdrops: {len(data.get('backdrops', []))}")
    print(f"  Symbols: {len(data.get('symbols', []))}")
    
    # Save to file
    output_file = 'gifts_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Saved to {output_file}")
    
    # Show sample gifts
    if data.get('gifts'):
        print("\n🎁 Sample gifts:")
        for gift in data['gifts'][:5]:
            print(f"  - {gift['full_name']}: ${gift['floor_price']} (Supply: {gift['supply']:,})")


if __name__ == '__main__':
    asyncio.run(main())
