#!/usr/bin/env python3
import requests
import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

USER_TOKEN = "9a9d7375-55da-45e3-a886-65cd197812bb"
MRKT_API_BASE = 'https://api.tgmrkt.io'

def find_by_name(name):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Authorization": f"Bearer {USER_TOKEN}"
    }

    from urllib.parse import quote
    url = f"{MRKT_API_BASE}/api/v1/gifts/search?q={quote(name)}"
    logger.info(f"Searching for {name} via {url}...")
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data:
                print(f"\n--- RESULTS FOR {name} ({len(data)}) ---")
                for item in data:
                    print(f"Name: {item.get('name')} | Title: {item.get('title')} | ID: {item.get('id')} | ImageKey: {item.get('modelStickerThumbnailKey') or item.get('thumbnailKey')}")
            else:
                print(f"No results for {name}")
        else:
            print(f"Error {r.status_code}: {r.text}")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    import sys
    search_term = sys.argv[1] if len(sys.argv) > 1 else "Teddie"
    find_by_name(search_term)
