#!/usr/bin/env python3
import os
import requests
import logging
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

STICKER_COLLECTIONS_DIR = "/root/01studio/giftschart/sticker_collections"
BASE_URL = "https://storage.googleapis.com/goodies-api-prod.firebasestorage.app/images/collection/"

# Mapping of NEW missing Goodies found in audit
# Format: (Col_UUID, Char_UUID, Coll_Norm, Sticker_Norm)
# For BONK, we use the DISCOVERED ID from browser (0c3b9f15...) instead of the database one
SUPPLEMENTAL_MAPPING = [
    # Blindbox items - Use the "ball" from cleeviox
    ('364e0ddc-7998-4e50-9831-a83dcc02a114', 'BALL_ASSET', 'goodies_blindbox', 'box_box_boxie'),
    ('364e0ddc-7998-4e50-9831-a83dcc02a114', 'BALL_ASSET', 'goodies_blindbox', 'masters_drop'),
    ('364e0ddc-7998-4e50-9831-a83dcc02a114', 'BALL_ASSET', 'goodies_blindbox', 'teddie_s_goodies'),
    ('364e0ddc-7998-4e50-9831-a83dcc02a114', 'BALL_ASSET', 'goodies_blindbox', 'monsters_unleashed_icons_of_horror'),
    ('364e0ddc-7998-4e50-9831-a83dcc02a114', 'BALL_ASSET', 'goodies_blindbox', 'lamborghini'),
    ('364e0ddc-7998-4e50-9831-a83dcc02a114', 'BALL_ASSET', 'goodies_blindbox', 'be_cool'),
    ('364e0ddc-7998-4e50-9831-a83dcc02a114', 'BALL_ASSET', 'goodies_blindbox', 'conviction_or_capitulation'),
    ('364e0ddc-7998-4e50-9831-a83dcc02a114', 'BALL_ASSET', 'goodies_blindbox', 'origin_of_the_birb'),

    # BONK - Use discovered ID: 0c3b9f15-f97c-41a7-b2f8-fde69bf77e5f
    ('babaa07e-7977-4b77-8c3b-5544710156d6', '0c3b9f15-f97c-41a7-b2f8-fde69bf77e5f', 'bonk', 'bonk_the_dog'),
    ('babaa07e-7977-4b77-8c3b-5544710156d6', '0c3b9f15-f97c-41a7-b2f8-fde69bf77e5f', 'bonk', 'bonk_hit_harder'),

    # Meebits/Neiro/Steady already worked, keeping just in case (optional, relying on existing files)
]

def download_asset(char_id, save_path):
    if char_id == 'BALL_ASSET':
        url = "https://goodies.cleeviox.com/assets/ball.png"
    else:
        url = f"{BASE_URL}{char_id}"
    
    try:
        logger.info(f"Downloading {url}...")
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            # Load as image and convert to WebP
            img = Image.open(io.BytesIO(r.content))
            img.save(save_path, 'WEBP', quality=95)
            logger.info(f"Saved to {save_path}")
            return True
        else:
            logger.error(f"Failed {r.status_code} for {char_id}")
            return False
    except Exception as e:
        logger.error(f"Error downloading {char_id}: {e}")
        return False

def main():
    success = 0
    fail = 0

    for col_uuid, char_id, coll_norm, sticker_norm in SUPPLEMENTAL_MAPPING:
        # Create directories
        sticker_dir = os.path.join(STICKER_COLLECTIONS_DIR, coll_norm, sticker_norm)
        os.makedirs(sticker_dir, exist_ok=True)
        dest_path = os.path.join(sticker_dir, "1.webp")
        
        if download_asset(char_id, dest_path):
            success += 1
        else:
            fail += 1
        
    logger.info(f"DONE. Success: {success}, Fail: {fail}")

if __name__ == "__main__":
    main()
