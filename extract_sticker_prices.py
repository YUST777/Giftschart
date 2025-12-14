#!/usr/bin/env python3
"""
Extract all sticker names and prices from the MRKT API
"""

import mrkt_api_improved as mrkt_api
import json
import os
from tabulate import tabulate
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('extract_sticker_prices')

# Get script directory for cross-platform compatibility
script_dir = os.path.dirname(os.path.abspath(__file__))

# Constants - use os.path.join for cross-platform compatibility
output_file = os.path.join(script_dir, "all_sticker_prices.json")

def main():
    """Extract all sticker names and prices from the MRKT API"""
    print("Fetching character data from API...")
    characters = mrkt_api.fetch_characters()
    
    stickers = []
    for char in characters:
        collection_name = char.get("collection", {}).get("name", "Unknown")
        character_name = char.get("name", "Unknown")
        price_nano_ton = char.get("price", 0)
        
        # Skip stickers with no price
        if price_nano_ton == 0:
            continue
            
        # Convert from nano TON to TON
        price_ton = mrkt_api.convert_nano_ton(price_nano_ton)
        # Get real TON price
        try:
            from ton_price_utils import get_ton_price_usd
            ton_price_usd = get_ton_price_usd()
        except ImportError:
            ton_price_usd = 2.10  # Fallback value
        price_usd = price_ton * ton_price_usd
        
        stickers.append({
            "collection": collection_name,
            "character": character_name,
            "price_ton": price_ton,
            "price_usd": price_usd
        })
    
    # Sort by price (highest first)
    stickers.sort(key=lambda x: x["price_ton"], reverse=True)
    
    # Save to JSON
    with open(output_file, "w") as f:
        json.dump(stickers, f, indent=2)
    
    print(f"Extracted {len(stickers)} stickers to {output_file}")
    
    # Print as table
    table_data = []
    for sticker in stickers:
        table_data.append([
            sticker['character'],
            f"{sticker['price_ton']:.2f} TON",
            f"${sticker['price_usd']:.2f}",
            sticker['collection']
        ])
    
    print("\n===== All Stickers Sorted by Price (Highest to Lowest) =====\n")
    print(tabulate(table_data, headers=['Name', 'Price (TON)', 'Price (USD)', 'Collection']))
    print(f"\nTotal stickers: {len(stickers)}")

if __name__ == "__main__":
    main() 