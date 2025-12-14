#!/usr/bin/env python3
"""
Update Sticker Supply

This script fetches supply information for stickers from the MRKT API
and updates the sticker_price_results.json file with this data.
"""

import os
import json
import logging
import datetime
import mrkt_api_improved as mrkt_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("update_sticker_supply")

# Get script directory for cross-platform compatibility
script_dir = os.path.dirname(os.path.abspath(__file__))
# File paths
PRICE_DATA_FILE = "sticker_price_results.json"
MAPPING_FILE = "mrkt_sticker_mapping.json"

def load_price_data():
    """Load price data from the JSON file"""
    try:
        with open(PRICE_DATA_FILE, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error loading price data: {e}")
        return None

def load_mapping_data():
    """Load mapping data from the JSON file"""
    try:
        with open(MAPPING_FILE, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error loading mapping data: {e}")
        return None

def save_price_data(data):
    """Save price data to the JSON file"""
    try:
        with open(PRICE_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Price data saved to {PRICE_DATA_FILE}")
    except Exception as e:
        logger.error(f"Error saving price data: {e}")

def update_sticker_supply():
    """Update sticker supply information from MRKT API"""
    # Load existing price data
    price_data = load_price_data()
    if not price_data:
        logger.error("Failed to load price data")
        return False
    
    # Load mapping data
    mapping_data = load_mapping_data()
    if not mapping_data:
        logger.error("Failed to load mapping data")
        return False
    
    # Fetch all stickers from API
    logger.info("Fetching stickers from MRKT API...")
    stickers_data = mrkt_api.fetch_characters(use_cache=False)
    
    if not stickers_data:
        logger.error("Failed to fetch stickers from MRKT API")
        return False
    
    logger.info(f"Fetched {len(stickers_data)} stickers from MRKT API")
    
    # Create a lookup dictionary from API data
    api_stickers = {}
    for sticker in stickers_data:
        collection_id = sticker.get('stickerCollectionId')
        sticker_id = sticker.get('id')
        key = f"{collection_id}:{sticker_id}"
        
        api_stickers[key] = {
            'name': sticker.get('name', ''),
            'price': sticker.get('floorPriceNanoTons', 0) or 0,
            'supply': sticker.get('supply', 0) or 0
        }
    
    # Update supply information in price data
    updated_count = 0
    for item in price_data['stickers_with_prices']:
        collection = item['collection']
        sticker = item['sticker']
        
        # Find API key for this sticker
        local_format = f"{collection} - {sticker}"
        api_key = None
        
        for key, value in mapping_data['sticker_mapping'].items():
            if value.get('local_format') == local_format:
                api_key = key
                break
        
        if api_key and api_key in api_stickers:
            api_data = api_stickers[api_key]
            item['supply'] = api_data['supply']
            updated_count += 1
        else:
            # If no mapping found, try direct name matching
            for key, api_data in api_stickers.items():
                if api_data['name'] == sticker:
                    item['supply'] = api_data['supply']
                    updated_count += 1
                    break
    
    # Update timestamp
    price_data['timestamp'] = datetime.datetime.now().isoformat()
    
    # Save updated price data
    save_price_data(price_data)
    
    logger.info(f"Updated supply information for {updated_count} stickers")
    return True

def main():
    """Main function"""
    logger.info("Updating sticker supply information...")
    update_sticker_supply()
    logger.info("Done!")

if __name__ == "__main__":
    main() 