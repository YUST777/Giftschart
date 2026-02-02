#!/usr/bin/env python3
import requests
import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Use the base URL found in mrkt_quant_api.py
MRKT_API_BASE = "https://api.tgmrkt.io"
# User's token from fetch_all_mrkt_data.py
USER_TOKEN = "9a9d7375-55da-45e3-a886-65cd197812bb"

GOODIES_NAMES = [
    "Teddie",
    "Oracle Red Bull Racing",
    "Not Wise",
    "WSB",
    "Cool Cats",
    "Doodles",
    "Moonbirds",
    "Pudgy Penguins x Kung Fu Panda",
    "Lamborghini"
]

def discover():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Authorization": f"Bearer {USER_TOKEN}"
    }

    # Common pattern in the codebase
    url = f"{MRKT_API_BASE}/api/v1/gifts/collections"
    logger.info(f"Fetching collections from {url}...")
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        logger.info(f"Status Code: {r.status_code}")
        
        if r.status_code != 200:
            logger.error(f"API Error: {r.status_code} - {r.text[:500]}")
            # Try a different endpoint if this one fails
            url_alt = f"{MRKT_API_BASE}/api/v1/stickers/collections"
            logger.info(f"Retrying with alternative endpoint: {url_alt}")
            r = requests.get(url_alt, headers=headers, timeout=15)
            logger.info(f"Alternative Status Code: {r.status_code}")
            
            if r.status_code != 200:
                return

        collections = r.json()
        logger.info(f"Found {len(collections)} collections.")
        
        found_map = {}

        for name in GOODIES_NAMES:
            logger.info(f"Searching for: {name}")
            for item in collections:
                coll_name = item.get('name', '')
                coll_title = item.get('title', '')
                
                # Case-insensitive partial match
                if name.lower() in coll_name.lower() or name.lower() in coll_title.lower():
                    logger.info(f"  MATCH: {coll_name} / {coll_title} (ID: {item.get('id')})")
                    if name not in found_map:
                        found_map[name] = []
                    found_map[name].append(item)

        # Save findings
        with open('goodies_discovery_results.json', 'w') as f:
            json.dump(found_map, f, indent=2)
        
        logger.info(f"Discovery complete. Results saved to goodies_discovery_results.json")
        
    except Exception as e:
        logger.error(f"Discovery failed: {e}")

if __name__ == "__main__":
    discover()
