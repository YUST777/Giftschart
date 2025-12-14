#!/usr/bin/env python3
"""
Test real API integration with MRKT and Quant
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_real_api():
    """Test real API data fetching"""
    import mrkt_quant_api
    
    print("=" * 80)
    print("Testing Real MRKT/Quant API Integration")
    print("=" * 80)
    print()
    
    # Test MRKT gifts (special numeric ID gifts)
    mrkt_gifts = ["Coffin", "Mask"]
    
    # Test Quant gifts
    quant_gifts = ["Backpack", "Book"]
    
    print("Testing MRKT API (Special Gifts with Numeric IDs)")
    print("-" * 80)
    for gift_name in mrkt_gifts:
        print(f"\nFetching: {gift_name}")
        try:
            data = await mrkt_quant_api.fetch_gift_data(gift_name)
            if data:
                print(f"✅ SUCCESS")
                print(f"   Price TON: {data.get('priceTon', 'N/A')}")
                print(f"   Price USD: {data.get('priceUsd', 'N/A')}")
                print(f"   Change %: {data.get('changePercentage', 'N/A')}")
                print(f"   Supply: {data.get('upgradedSupply', 'N/A')}")
            else:
                print(f"❌ No data returned")
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 80)
    print("Testing Quant API")
    print("-" * 80)
    for gift_name in quant_gifts:
        print(f"\nFetching: {gift_name}")
        try:
            data = await mrkt_quant_api.fetch_gift_data(gift_name)
            if data:
                print(f"✅ SUCCESS")
                print(f"   Price TON: {data.get('priceTon', 'N/A')}")
                print(f"   Price USD: {data.get('priceUsd', 'N/A')}")
                print(f"   Change %: {data.get('changePercentage', 'N/A')}")
                print(f"   Supply: {data.get('upgradedSupply', 'N/A')}")
            else:
                print(f"❌ No data returned")
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_real_api())

