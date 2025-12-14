#!/usr/bin/env python3
"""
Compare Cached Prices with Live Prices

This script compares the cached sticker prices from the JSON file
with the live prices fetched directly from the MRKT API.
"""

import os
import sys
import json
import logging
import argparse
import stickers_tools_api as sticker_api
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("compare_prices")

# Get script directory for cross-platform compatibility
script_dir = os.path.dirname(os.path.abspath(__file__))

# Constants - use os.path.join for cross-platform compatibility
PRICE_DATA_FILE = os.path.join(script_dir, "sticker_price_results.json")
OUTPUT_FILE = os.path.join(script_dir, "price_comparison_results.json")

def load_cached_prices():
    """Load cached price data from the JSON file"""
    try:
        with open(PRICE_DATA_FILE, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error loading price data: {e}")
        return None

def get_live_price(collection, sticker):
    price_info = sticker_api.get_sticker_price(collection, sticker, force_refresh=True)
    if price_info and "floor_price_ton" in price_info:
        return price_info["floor_price_ton"]
    return None

def compare_prices(limit=None):
    """Compare cached prices with live prices"""
    cached_data = load_cached_prices()
    
    if not cached_data or 'stickers_with_prices' not in cached_data:
        logger.error("Invalid or missing cached price data")
        return False
    
    # Get the timestamp from the cached data
    cached_timestamp = cached_data.get('timestamp', 'Unknown')
    cached_date = datetime.fromtimestamp(cached_timestamp).strftime('%Y-%m-%d %H:%M:%S') if isinstance(cached_timestamp, (int, float)) else cached_timestamp
    
    # Current timestamp
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Initialize results
    results = {
        "cached_timestamp": cached_date,
        "live_timestamp": current_timestamp,
        "comparisons": []
    }
    
    # Counter for successful API calls
    successful = 0
    failed = 0
    
    # Process stickers
    stickers = cached_data['stickers_with_prices']
    if limit:
        stickers = stickers[:limit]
    
    total = len(stickers)
    print(f"Comparing prices for {total} stickers...")
    
    for i, sticker_data in enumerate(stickers):
        collection = sticker_data['collection']
        sticker = sticker_data['sticker']
        cached_price = sticker_data.get('price')
        supply = sticker_data.get('supply')
        
        print(f"[{i+1}/{total}] Checking {collection} - {sticker}...")
        
        # Get live price
        live_price = get_live_price(collection, sticker)
        
        if live_price is not None:
            successful += 1
            price_diff = live_price - cached_price if cached_price else 0
            percent_change = (price_diff / cached_price * 100) if cached_price else 0
            
            comparison = {
                "collection": collection,
                "sticker": sticker,
                "cached_price": cached_price,
                "live_price": live_price,
                "difference": price_diff,
                "percent_change": percent_change,
                "supply": supply
            }
            
            results["comparisons"].append(comparison)
            
            # Print comparison
            change_symbol = "🔺" if price_diff > 0 else "🔻" if price_diff < 0 else "◼️"
            print(f"  {change_symbol} {collection} - {sticker}: {cached_price} TON → {live_price} TON ({percent_change:.2f}%)")
        else:
            failed += 1
            print(f"  ❌ Failed to get live price for {collection} - {sticker}")
    
    # Save results to file
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nComparison complete: {successful} successful, {failed} failed")
    print(f"Results saved to {OUTPUT_FILE}")
    
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Compare cached prices with live prices")
    parser.add_argument("--limit", type=int, help="Limit the number of stickers to compare")
    
    args = parser.parse_args()
    
    # Compare prices
    compare_prices(args.limit)

if __name__ == "__main__":
    main() 