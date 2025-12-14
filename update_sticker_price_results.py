#!/usr/bin/env python3
"""
Update Sticker Price Results

This script updates the sticker price results with fresh data from the MRKT API.
It keeps the existing supply data but updates the prices with live data.
"""

import os
import sys
import json
import logging
import time
from datetime import datetime
import stickers_tools_api as sticker_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("update_sticker_price_results")

# Get script directory for cross-platform compatibility
script_dir = os.path.dirname(os.path.abspath(__file__))

# Constants - use os.path.join for cross-platform compatibility
PRICE_DATA_FILE = os.path.join(script_dir, "sticker_price_results.json")

def load_existing_data():
    """Load existing price data from the JSON file"""
    try:
        if os.path.exists(PRICE_DATA_FILE):
            with open(PRICE_DATA_FILE, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded existing price data with {len(data.get('stickers_with_prices', []))} stickers")
                return data
        else:
            logger.warning(f"Price file not found: {PRICE_DATA_FILE}")
            return {
                "timestamp": datetime.now().isoformat(),
                "total_templates": 0,
                "successful": 0,
                "failed": 0,
                "stickers_with_prices": []
            }
    except Exception as e:
        logger.error(f"Error loading price data: {e}")
        return None

def save_updated_data(data):
    """Save updated price data to the JSON file"""
    try:
        with open(PRICE_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Updated price data saved to {PRICE_DATA_FILE}")
    except Exception as e:
        logger.error(f"Error saving price data: {e}")

def update_prices():
    """Update prices with fresh data from the MRKT API"""
    # Load existing data
    data = load_existing_data()
    if not data:
        logger.error("Failed to load existing data")
        return
    
    # Update timestamp
    data["timestamp"] = datetime.now().isoformat()
    
    # Track results
    updated_count = 0
    failed_count = 0
    
    # Update each sticker's price
    for i, sticker_data in enumerate(data["stickers_with_prices"]):
        collection = sticker_data["collection"]
        sticker = sticker_data["sticker"]
        logger.info(f"Updating price for {collection} {sticker} ({i+1}/{len(data['stickers_with_prices'])})")
        try:
            price_info = sticker_api.get_sticker_price(collection, sticker, force_refresh=True)
            if price_info and price_info['floor_price_ton'] > 0:
                old_price = sticker_data.get("price", 0)
                new_price = price_info['floor_price_ton']
                sticker_data["price"] = new_price
                price_change = ((new_price - old_price) / old_price) * 100 if old_price > 0 else 0
                sticker_data["price_change_percent"] = round(price_change, 2)
                logger.info(f"✅ Updated price for {collection} {sticker}: {old_price} → {new_price} TON ({price_change:.2f}%)")
                updated_count += 1
            else:
                logger.warning(f"⚠️ No real price data for {collection} {sticker}")
                failed_count += 1
        except Exception as e:
            logger.error(f"❌ Error updating price for {collection} {sticker}: {e}")
            failed_count += 1
        
        # Add a small delay to avoid rate limiting
        time.sleep(0.5)
    
    # Update success counts
    data["successful"] = updated_count
    data["failed"] = failed_count
    
    # Save updated data
    save_updated_data(data)
    
    logger.info(f"Price update complete: {updated_count} updated, {failed_count} failed")

if __name__ == "__main__":
    # Test API connection
    logger.info("Testing MRKT API connection...")
    # Remove any call to sticker_api.get_working_token() and related MRKT API test logic.
        update_prices()