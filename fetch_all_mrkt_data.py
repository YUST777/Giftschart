
import requests
import json
import logging

# User's token
USER_TOKEN = "9a9d7375-55da-45e3-a886-65cd197812bb"
MRKT_API_BASE = 'https://api.tgmrkt.io'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_all():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Authorization": f"Bearer {USER_TOKEN}"
    }

    # Endpoint 1: gifts/collections (from mrkt_quant_api.py)
    url1 = f"{MRKT_API_BASE}/api/v1/gifts/collections"
    logger.info(f"Fetching {url1}...")
    try:
        r = requests.get(url1, headers=headers, timeout=15)
        print(f"URL1 Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"URL1 Count: {len(data)}")
            # Dump first item to see structure
            if data:
                print("Sample URL1 item:", json.dumps(data[0], indent=2))
                
            # Print all names to see if Hot Cherry is there
            print("\n--- URL1 NAMES ---")
            found = False
            for item in data:
                name = item.get('name')
                title = item.get('title')
                print(f"{name} / {title}")
                if 'Cherry' in str(title) or 'Cherry' in str(name):
                    print("!!! FOUND CHERRY !!!")
                    print(json.dumps(item, indent=2))
                    found = True
            if not found:
                 print("XXX Hot Cherry NOT found in URL1")
        else:
            print(r.text[:200])
    except Exception as e:
        logger.error(f"URL1 Error: {e}")

    # Endpoint 2: Guessing /api/v1/sticker-sets (without IDs?)
    # or /api/v1/sticker-sets/all ?
    
if __name__ == "__main__":
    fetch_all()
