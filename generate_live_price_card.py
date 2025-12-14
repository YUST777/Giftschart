#!/usr/bin/env python3
"""
Generate Live Price Card

This script generates a price card for a sticker using live data from the MRKT API.
It bypasses the cached supply data and fetches real-time price information.
"""

import os
import sys
import json
import logging
import argparse
import stickers_tools_api as sticker_api
import sticker_price_card_generator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("generate_live_price_card")

# Get script directory for cross-platform compatibility
script_dir = os.path.dirname(os.path.abspath(__file__))

# Constants - use os.path.join for cross-platform compatibility
OUTPUT_DIR = os.path.join(script_dir, "Sticker_Price_Cards")

def generate_live_price_card(collection, sticker):
    """Generate a price card using live data from the MRKT API"""
    logger.info(f"Generating live price card for {collection} - {sticker}")
    price_info = sticker_api.get_sticker_price(collection, sticker, force_refresh=True)
    if not price_info or 'floor_price_ton' not in price_info:
        logger.error(f"Failed to get price data for {collection} {sticker}")
        print(f"❌ ERROR: Could not get live price data for {collection} - {sticker}")
        return False
    price = price_info['floor_price_ton']
    print(f"🌐 LIVE API: Got fresh price data for {collection} - {sticker}: {price} TON")
    
    # Generate the card with the live price
    result = sticker_price_card_generator.generate_price_card(
        collection, 
        sticker, 
        price, 
        OUTPUT_DIR, 
        price_data=None,
        use_cached_supply=False
    )
    
    if result:
        print(f"✅ Successfully generated live price card for {collection} - {sticker}")
        print(f"📊 Cache usage stats: {sticker_price_card_generator.cached_usage} from cache, {sticker_price_card_generator.live_api_usage} from live API")
    else:
        print(f"❌ Failed to generate live price card for {collection} - {sticker}")
    
    return result

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate a price card using live data from the MRKT API")
    parser.add_argument("--collection", required=True, help="Sticker collection name")
    parser.add_argument("--sticker", required=True, help="Sticker name")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory for generated cards")
    
    args = parser.parse_args()
    
    # Generate the card
    generate_live_price_card(args.collection, args.sticker)

if __name__ == "__main__":
    main() 