import requests
import json
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_TOKEN = "9a9d7375-55da-45e3-a886-65cd197812bb"
URL = "https://api.tgmrkt.io/api/v1/sticker-sets/characters"

def discover_range(start, end):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {USER_TOKEN}"
    }
    
    # Process in batches of 20 to avoid timeouts/limits
    batch_size = 20
    for i in range(start, end, batch_size):
        batch_end = min(i + batch_size, end)
        collection_ids = list(range(i, batch_end))
        
        payload = {"collections": collection_ids}
        logger.info(f"Scanning IDs {i} to {batch_end - 1}...")
        
        try:
            r = requests.post(URL, headers=headers, json=payload, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data:
                    for item in data:
                        c_id = item.get('collectionId') or item.get('col_id') # Guessing field name
                        name = item.get('name')
                        if not c_id:
                            # Try to infer ID from preview path or other data?
                            # Actually, the response is a list of characters.
                            # We can just print the character names and see if they match "Teddie"
                            pass
                        
                        logger.info(f"  FOUND: {name} (CharID: {item.get('id')})")
                        
                        if "Teddie" in name or "Lamborghini" in name:
                            print(f"\nmatch_found: {name} | Full Data: {json.dumps(item)[:200]}...\n")
                            # If we find a match, we essentially proved the ID is in this batch.
                            # But we need the COLLECTION ID.
                            # MRKT API usually returns the object.
                            # Let's see the full item structure for a match.
            else:
                logger.warning(f"  Status {r.status_code}")
        except Exception as e:
            logger.error(f"  Error: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    discover_range(61, 300)
