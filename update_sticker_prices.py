#!/usr/bin/env python3
"""
Update sticker prices with real data from the MRKT API

This script:
1. Reads existing price data from sticker_price_results.json
2. Updates prices with real data from the MRKT API where available
3. Saves the updated price data back to the file
"""

import os
import json
import time
import logging
from datetime import datetime
import stickers_tools_api as sticker_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("update_prices")

# Get script directory for cross-platform compatibility
script_dir = os.path.dirname(os.path.abspath(__file__))
# Path to the sticker price results file
PRICE_DATA_FILE = "sticker_price_results.json"

def load_existing_prices():
    """
    Load existing price data from sticker_price_results.json
    
    Returns:
        dict: Existing price data or empty dict if file doesn't exist
    """
    try:
        if os.path.exists(PRICE_DATA_FILE):
            with open(PRICE_DATA_FILE, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded existing price data with {len(data.get('stickers_with_prices', []))} entries")
                return data
        else:
            logger.warning(f"Price file not found: {PRICE_DATA_FILE}")
            return {"stickers_with_prices": [], "timestamp": time.time()}
    except Exception as e:
        logger.error(f"Error loading price data: {e}")
        return {"stickers_with_prices": [], "timestamp": time.time()}

def update_sticker_prices():
    """
    Update sticker prices with real data from stickers.tools API
    """
    existing_data = load_existing_prices()
    updated_count = 0
    failed_count = 0
    skipped_count = 0
    stickers = existing_data.get("stickers_with_prices", [])
    total_stickers = len(stickers)
    logger.info(f"Starting price update for {total_stickers} stickers")
    print(f"🔄 UPDATING: Refreshing prices for {total_stickers} stickers...")
    for i, sticker_data in enumerate(stickers):
        collection = sticker_data.get("collection", "")
        sticker = sticker_data.get("sticker", "")
        logger.info(f"Processing {i+1}/{total_stickers}: {collection} {sticker}")
        try:
            price_info = sticker_api.get_sticker_price(collection, sticker, force_refresh=False)
            if price_info and price_info["floor_price_ton"] > 0:
                sticker_data["price"] = price_info["floor_price_ton"]
                sticker_data["price_usd"] = price_info["floor_price_usd"]
                sticker_data["supply"] = price_info["supply"]
                sticker_data["median_price_ton"] = price_info["median_price_ton"]
                sticker_data["median_price_usd"] = price_info["median_price_usd"]
                sticker_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"✅ Updated price for {collection} - {sticker}: {price_info['floor_price_ton']} TON")
                print(f"  ✅ Updated: {collection} - {sticker}: {price_info['floor_price_ton']} TON")
                updated_count += 1
            else:
                logger.info(f"ℹ️ No price data for {collection} {sticker}")
                print(f"  ⚠️ No data: {collection} - {sticker}")
                skipped_count += 1
        except Exception as e:
            logger.error(f"Error updating price for {collection} {sticker}: {e}")
            print(f"  ❌ Failed: {collection} - {sticker}: {str(e)}")
            failed_count += 1
        time.sleep(0.5)
    existing_data["timestamp"] = time.time()
    with open(PRICE_DATA_FILE, 'w') as f:
        json.dump(existing_data, f, indent=2)
    logger.info(f"Update complete: {updated_count} updated, {skipped_count} skipped, {failed_count} failed.")
    print(f"✅ Update complete: {updated_count} updated, {skipped_count} skipped, {failed_count} failed.")

if __name__ == "__main__":
        update_sticker_prices()