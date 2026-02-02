import os
import json
from urllib.parse import quote

STICKER_COLLECTIONS_DIR = "/root/01studio/giftschart/sticker_collections"
STATS_FILE = "/root/01studio/giftschart/sticker_stats_dump.json"

def normalize_name(name):
    # Same normalization as in other scripts
    import re
    normalized = name.strip().lower()
    normalized = re.sub(r'[^a-z0-9]', '_', normalized)
    normalized = re.sub(r'_+', '_', normalized)
    return normalized.strip('_')

def main():
    print("Checking for missing assets...")
    
    # Load stats to get list of expected collections/stickers
    if not os.path.exists(STATS_FILE):
        print("Stats file not found.")
        return

    with open(STATS_FILE, 'r') as f:
        data = json.load(f)

    missing_count = 0
    total_checked = 0

    for col_key, col_data in data.get("collections", {}).items():
        col_name = col_data.get("name")
        col_norm = normalize_name(col_name)
        
        for sticker in col_data.get("stickers", []):
            sticker_name = sticker.get("name")
            if not sticker_name:
                continue
            sticker_norm = normalize_name(sticker_name)
            
            # Construct expected path
            # Most use 1.webp, but need to check if there's *any* image
            sticker_dir = os.path.join(STICKER_COLLECTIONS_DIR, col_norm, sticker_norm)
            
            total_checked += 1
            
            if not os.path.exists(sticker_dir):
                print(f"MISSING DIR: {col_name} -> {sticker_name} ({sticker_dir})")
                missing_count += 1
                continue
                
            # Check for valid image files
            files = os.listdir(sticker_dir)
            images = [f for f in files if f.endswith('.webp') or f.endswith('.png')]
            
            if not images:
                print(f"NO IMAGES: {col_name} -> {sticker_name} in {sticker_dir}")
                missing_count += 1
            else:
                # Check specifics if needed, but for now just existence
                pass

    print(f"\nScan complete. Checked {total_checked} stickers.")
    if missing_count == 0:
        print("✅ No missing asset directories/files found.")
    else:
        print(f"❌ Found {missing_count} missing assets.")

if __name__ == "__main__":
    main()
