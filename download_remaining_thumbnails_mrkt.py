import os
import json
import requests
import logging
import time
from fuzzywuzzy import fuzz, process

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# User's token (hardcoded from history)
USER_TOKEN = "9a9d7375-55da-45e3-a886-65cd197812bb"
CDN_BASE = "https://cdn.tgmrkt.io"

def normalize_name(name):
    import re
    normalized = name.strip().lower()
    normalized = re.sub(r'[^a-z0-9]', '_', normalized)
    normalized = re.sub(r'_+', '_', normalized)
    return normalized.strip('_')

def fetch_characters():
    logger.info("Fetching characters from MRKT API...")
    url = "https://api.tgmrkt.io/api/v1/sticker-sets/characters"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {USER_TOKEN}"
    }
    
    # Updated range to probe for newer collections (GOODIES/BONK might be here)
    collection_ids = list(range(1, 150))
    payload = {"collections": collection_ids}

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            return r.json()
        else:
            logger.error(f"Fetch failed: {r.status_code} {r.text[:200]}")
            return []
    except Exception as e:
        logger.error(f"Fetch error: {e}")
        return []

def main():
    logger.info("Starting download of remaining thumbnails (Standalone)...")
    
    base_dir = '/root/01studio/giftschart/sticker_collections'
    json_path = '/root/01studio/giftschart/sticker_price_results.json'
    
    if not os.path.exists(json_path):
        logger.error(f"JSON not found: {json_path}")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)
        
    stickers = data.get('stickers_with_prices', [])
    logger.info(f"Loaded {len(stickers)} stickers from database.")
    
    # Fetch API characters
    characters = fetch_characters()
    if not characters:
        logger.error("No characters fetched. Aborting.")
        return
    logger.info(f"Fetched {len(characters)} characters from API.")
    
    # Map characters by name for exact match
    char_map = {normalize_name(c.get('name', '')): c for c in characters}
    char_names = list(char_map.keys()) # For fuzzy matching
    
    logger.info(f"Loaded {len(char_names)} names from API. Examples: {char_names[:10]}")

    count_downloaded = 0
    count_skipped = 0
    count_not_found = 0
    
    for s in stickers:
        sticker_name = s.get('sticker')
        coll_name = s.get('collection')
        
        # Determine target file
        coll_norm = normalize_name(coll_name)
        sticker_norm = normalize_name(sticker_name)
        target_dir = os.path.join(base_dir, coll_norm, sticker_norm)
        target_file = os.path.join(target_dir, '1.webp')
        
        # Skip if exists
        if os.path.exists(target_file) and os.path.getsize(target_file) > 1000:
            count_skipped += 1
            continue
            
        logger.info(f"Processing missing: {coll_name} / {sticker_name}")
        
        # Match
        s_name_lower = sticker_name.lower()
        match_char = None
        
        # 1. Exact Name
        if s_name_lower in char_map:
            match_char = char_map[s_name_lower]
        
        # 2. Fuzzy Name
        if not match_char:
            best_match_name, score = process.extractOne(s_name_lower, char_names, scorer=fuzz.token_sort_ratio)
            if score > 70:
                match_char = char_map[best_match_name]
                logger.info(f"  -> Fuzzy match: {sticker_name} ~= {match_char.get('name')} ({score})")
        
        if match_char:
            preview = match_char.get('previewSticker', {})
            thumb_path = preview.get('thumbnail') or preview.get('preview')
            
            if thumb_path:
                url = f"{CDN_BASE}/{thumb_path}"
                try:
                    r = requests.get(url, timeout=10)
                    if r.status_code == 200:
                        os.makedirs(target_dir, exist_ok=True)
                        with open(target_file, 'wb') as f:
                            f.write(r.content)
                        logger.info(f"  ✅ Downloaded: {url}")
                        count_downloaded += 1
                    else:
                        logger.warning(f"  ❌ HTTP {r.status_code}")
                except Exception as e:
                     logger.error(f"  ❌ Download Error: {e}")
            else:
                logger.warning("  ❌ No thumbnail URL in API")
        else:
            logger.warning("  ❌ No match found")
            count_not_found += 1
            
    logger.info("="*50)
    logger.info(f"Summary:")
    logger.info(f"  Existing: {count_skipped}")
    logger.info(f"  Downloaded: {count_downloaded}")
    logger.info(f"  Not Found: {count_not_found}")
    
if __name__ == "__main__":
    main()
