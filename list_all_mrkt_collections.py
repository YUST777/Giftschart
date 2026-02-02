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

def list_all():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Authorization": f"Bearer {USER_TOKEN}"
    }

    url = f"{MRKT_API_BASE}/api/v1/gifts/collections"
    logger.info(f"Fetching {url}...")
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            print(f"\n--- ALL MRKT COLLECTIONS ({len(data)}) ---")
            for item in data:
                print(f"ID: {item.get('id')} | Name: {item.get('name')} | Title: {item.get('title')}")
        else:
            print(f"Error: {r.status_code}")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    list_all()
