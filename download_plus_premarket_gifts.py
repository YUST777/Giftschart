#!/usr/bin/env python3
"""
Download Plus Premarket Gift Images
Downloads the 29 plus premarket gift images from Telegram CDN
"""

import os
import requests
import time
import logging
from plus_premarket_gifts import PLUS_PREMARKET_GIFTS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
output_folder = os.path.join(script_dir, "downloaded_images")

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Base URL for gift images
BASE_URL = "https://cdn.changes.tg/gifts/originals/{}/Original.webp"

def download_image(gift_id, filename, gift_name):
    """Download a single gift image"""
    url = BASE_URL.format(gift_id)
    filepath = os.path.join(output_folder, filename)
    
    # Skip if file already exists
    if os.path.exists(filepath):
        logger.info(f"✓ Already exists: {filename}")
        return True
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Downloading {gift_name} (ID: {gift_id})...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✓ Downloaded: {filename} ({len(response.content)} bytes)")
            return True
            
        except requests.RequestException as e:
            logger.error(f"✗ Attempt {attempt+1}/{max_retries} failed for {gift_name}: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"  Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error(f"✗ Failed to download {gift_name} after {max_retries} attempts")
                return False
    
    return False

def main():
    """Download all plus premarket gift images"""
    print("=" * 80)
    print("Plus Premarket Gifts Image Downloader")
    print("=" * 80)
    print(f"Downloading {len(PLUS_PREMARKET_GIFTS)} gift images...")
    print(f"Output folder: {output_folder}")
    print()
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    for normalized_name, gift_info in PLUS_PREMARKET_GIFTS.items():
        gift_name = gift_info["name"]
        gift_id = gift_info["id"]
        filename = f"{normalized_name}.webp"
        
        # Check if already exists
        filepath = os.path.join(output_folder, filename)
        if os.path.exists(filepath):
            skip_count += 1
            logger.info(f"✓ Already exists: {filename}")
            continue
        
        # Download the image
        if download_image(gift_id, filename, gift_name):
            success_count += 1
        else:
            fail_count += 1
        
        # Small delay between downloads to be nice to the server
        time.sleep(0.5)
    
    print()
    print("=" * 80)
    print("Download Summary")
    print("=" * 80)
    print(f"Total gifts:      {len(PLUS_PREMARKET_GIFTS)}")
    print(f"Already existed:  {skip_count}")
    print(f"Downloaded:       {success_count}")
    print(f"Failed:           {fail_count}")
    print("=" * 80)
    
    if fail_count > 0:
        print("\n⚠ Some downloads failed. Check the log above for details.")
        return 1
    else:
        print("\n✓ All gift images are ready!")
        return 0

if __name__ == "__main__":
    exit(main())

