import os
import json
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_name(name):
    """Normalize name for directory compatibility"""
    # Simply strip trailing underscores or special chars if needed
    # But here we are reading FROM directories, so we want the human readable name?
    # Actually, the directory name IS the normalized name.
    # We might need to guess the original name or just use the dir name as the key.
    return name

def main():
    base_dir = '/root/01studio/giftschart/sticker_collections'
    output_file = '/root/01studio/giftschart/sticker_price_results.json'
    
    if not os.path.exists(base_dir):
        logger.error(f"Directory not found: {base_dir}")
        return

    stickers_list = []
    
    logger.info(f"Scanning {base_dir}...")
    
    # Iterate over collection folders
    for coll_dir in os.listdir(base_dir):
        coll_path = os.path.join(base_dir, coll_dir)
        if not os.path.isdir(coll_path):
            continue
            
        # Iterate over sticker folders within collection
        for sticker_dir in os.listdir(coll_path):
            sticker_path = os.path.join(coll_path, sticker_dir)
            if not os.path.isdir(sticker_path):
                continue
                
            # Create entry
            # We use the directory names as the collection/sticker/name for now
            # because we don't have the original pretty names.
            # Hopefully the fuzzy matcher in the downloader can handle "bored_stickers" vs "Bored Stickers"
            
            entry = {
                "collection": coll_dir,  # e.g. "bored_stickers"
                "sticker": sticker_dir,  # e.g. "3278"
                "price": 0,
                "floor_price_ton": 0,
                "supply": 0
            }
            stickers_list.append(entry)
            
    logger.info(f"Found {len(stickers_list)} stickers.")
    
    output_data = {
        "timestamp": 0,
        "stickers_with_prices": stickers_list
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
        
    logger.info(f"Saved to {output_file}")

if __name__ == "__main__":
    main()
