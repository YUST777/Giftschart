import os
import json
import re

def normalize_name(name):
    normalized = name.strip().lower()
    normalized = re.sub(r'[^a-z0-9]', '_', normalized)
    normalized = re.sub(r'_+', '_', normalized)
    return normalized.strip('_')

def main():
    base_dir = '/root/01studio/giftschart/sticker_collections'
    json_path = '/root/01studio/giftschart/sticker_price_results.json'

    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)

    missing_count = 0
    total_count = 0
    
    print("="*60)
    print("MISSING STICKER THUMBNAILS REPORT")
    print("="*60)
    print(f"{'Collection':<30} | {'Sticker Name':<30} | {'Expected Path'}")
    print("-" * 100)

    for sticker in data.get('stickers_with_prices', []):
        total_count += 1
        coll_name = sticker.get('collection', 'Unknown')
        sticker_name = sticker.get('sticker', 'Unknown')

        # Normalize names
        coll_norm = normalize_name(coll_name)
        sticker_norm = normalize_name(sticker_name)

        # Expected path
        expected_dir = os.path.join(base_dir, coll_norm, sticker_norm)
        expected_file = os.path.join(expected_dir, '1.webp')

        if not os.path.exists(expected_file):
            missing_count += 1
            rel_path = f"sticker_collections/{coll_norm}/{sticker_norm}/1.webp"
            print(f"{coll_name:<30} | {sticker_name:<30} | {rel_path}")

    print("-" * 100)
    print(f"Total Stickers: {total_count}")
    print(f"Missing Thumbnails: {missing_count}")
    print("="*60)

if __name__ == "__main__":
    main()
