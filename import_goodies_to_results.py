import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RESULTS_PATH = "/root/01studio/giftschart/sticker_price_results.json"
DUMP_PATH = "/root/01studio/giftschart/sticker_stats_dump.json"

GOODIES_COLLECTIONS = [
    "Teddie", "Lamborghini", "Oracle Red Bull Racing", "NOT Wise", "WSB", 
    "Cool Cats", "Doodles", "Moonbirds", "Pudgy Penguins x Kung Fu Panda"
]

def normalize_name(name):
    import re
    normalized = name.strip().lower()
    normalized = re.sub(r'[^a-z0-9]', '_', normalized)
    normalized = re.sub(r'_+', '_', normalized)
    return normalized.strip('_')

def main():
    if not os.path.exists(RESULTS_PATH) or not os.path.exists(DUMP_PATH):
        logger.error("Files missing.")
        return

    with open(RESULTS_PATH, 'r') as f:
        results = json.load(f)
    
    with open(DUMP_PATH, 'r') as f:
        dump = json.load(f)

    # Convert results list to dict for easier lookup temporarily? 
    # Actually results is likely { "stickers_with_prices": [...] }
    if "stickers_with_prices" not in results:
        results["stickers_with_prices"] = []
    
    current_stickers = results["stickers_with_prices"]
    # Create a set of existing (coll, name) tuples
    existing = set((s.get('collection'), s.get('sticker')) for s in current_stickers)
    
    added_count = 0
    
    # Iterate through dump to find Goodies
    for coll_id, coll_data in dump.get("collections", {}).items():
        coll_name = coll_data.get("name")
        
        # Check if it's a target collection
        if coll_name in GOODIES_COLLECTIONS:
            logger.info(f"Processing collection: {coll_name}")
            
            for sticker in coll_data.get("stickers", []):
                s_name = sticker.get("name")
                
                if not s_name:
                    continue

                if (coll_name, s_name) in existing:
                    continue
                
                # Construct new entry matching the format
                new_entry = {
                    "collection": coll_name,
                    "sticker": s_name,
                    "price": sticker.get("floor_price_ton", "0"), # Default to floor or 0
                    "change": sticker.get("floor_change_24h_ton", "0%"),
                    "volume": sticker.get("24h_volume_ton", "0"),
                     # Add other fields if needed by generator, but these are main ones
                    "image_path": f"/root/01studio/giftschart/sticker_collections/{normalize_name(coll_name)}/{normalize_name(s_name)}/1.webp" 
                }
                
                current_stickers.append(new_entry)
                added_count += 1
                logger.info(f"  Added: {s_name}")

    if added_count > 0:
        with open(RESULTS_PATH, 'w') as f:
            json.dump(results, f, indent=4)
        logger.info(f"Successfully added {added_count} Goodies to database.")
    else:
        logger.info("No new Goodies added (already exist or not found).")

if __name__ == "__main__":
    main()
