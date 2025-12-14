#!/usr/bin/env python3
"""
Fetch prices for new premarket gifts (2025 releases)
Uses Tonnel API to get current prices for:
- Happy Brownie
- Spring Basket
- Instant Ramen
- Faith Amulet
- Mousse Cake
- Ice Cream
"""

import asyncio
import logging
import sys
from datetime import datetime
from tonnel_api import get_tonnel_gift_price, PREMARKET_GIFTS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def fetch_new_premarket_prices():
    """Fetch prices for all new premarket gifts."""
    
    print("=" * 70)
    print("🎁 NEW PREMARKET GIFTS - PRICE FETCH")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total gifts to fetch: {len(PREMARKET_GIFTS)}")
    print("=" * 70)
    print()
    
    results = {}
    successful = 0
    failed = 0
    
    for gift_key, gift_display_name in PREMARKET_GIFTS.items():
        print(f"🔍 Fetching price for: {gift_display_name}")
        print(f"   Internal name: {gift_key}")
        
        try:
            # Fetch price using Tonnel API
            price = await get_tonnel_gift_price(gift_key, force_fresh=True)
            
            if price is not None:
                print(f"   ✅ Success! Price: {price} TON")
                results[gift_display_name] = {
                    'price': price,
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                }
                successful += 1
            else:
                print(f"   ❌ Failed! No price available")
                results[gift_display_name] = {
                    'price': None,
                    'status': 'failed',
                    'timestamp': datetime.now().isoformat()
                }
                failed += 1
                
        except Exception as e:
            print(f"   💥 Error: {str(e)}")
            results[gift_display_name] = {
                'price': None,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            failed += 1
        
        print()
        
        # Small delay between requests to be respectful to the API
        await asyncio.sleep(2)
    
    # Print summary
    print("=" * 70)
    print("📊 FETCH SUMMARY")
    print("=" * 70)
    print(f"Total gifts: {len(PREMARKET_GIFTS)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(successful/len(PREMARKET_GIFTS)*100):.1f}%")
    print()
    
    # Print results table
    print("📋 RESULTS TABLE")
    print("-" * 70)
    print(f"{'Gift Name':<25} {'Price (TON)':<15} {'Status':<10}")
    print("-" * 70)
    
    for gift_name, data in results.items():
        price_str = f"{data['price']:.2f}" if data['price'] is not None else "N/A"
        status = data['status'].upper()
        print(f"{gift_name:<25} {price_str:<15} {status:<10}")
    
    print("-" * 70)
    print()
    
    # Show image paths
    print("📁 IMAGE FILE PATHS")
    print("-" * 70)
    image_paths = {
        "Happy Brownie": "/home/yousefmsm1/Desktop/3.7.5.2/downloaded_images/Happy_Brownie.png",
        "Spring Basket": "/home/yousefmsm1/Desktop/3.7.5.2/downloaded_images/Spring_Basket.png",
        "Instant Ramen": "/home/yousefmsm1/Desktop/3.7.5.2/downloaded_images/Instant_Ramen.png",
        "Faith Amulet": "/home/yousefmsm1/Desktop/3.7.5.2/downloaded_images/Faith_Amulet.png",
        "Mousse Cake": "/home/yousefmsm1/Desktop/3.7.5.2/downloaded_images/Mousse_Cake.png",
        "Ice Cream": "/home/yousefmsm1/Desktop/3.7.5.2/downloaded_images/Ice_Cream.png",
    }
    
    for gift_name, path in image_paths.items():
        print(f"{gift_name:<25} ✓ {path}")
    
    print("=" * 70)
    
    return results

async def main():
    """Main entry point."""
    try:
        results = await fetch_new_premarket_prices()
        
        # Save results to a file
        import json
        output_file = 'new_premarket_prices_results.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
        print("\n✅ Price fetch complete!")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Starting price fetch for new premarket gifts...")
    print()
    asyncio.run(main())

