import requests
import json
import logging
import time

# User's token
USER_TOKEN = "9a9d7375-55da-45e3-a886-65cd197812bb"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def discover_collections():
    url = "https://api.tgmrkt.io/api/v1/sticker-sets/characters"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {USER_TOKEN}"
    }
    
    # DEBUG: Check only ID 24
    # batch_ids = [24]
    
    # Check IDs 1 to 100 in batches of 10
    all_collections = {}
    
    for i in range(300, 601, 10):
        batch_ids = list(range(i, i + 10))
        # Remove 0 if present (IDs usually start at 1)
        if 0 in batch_ids: batch_ids.remove(0)
            
        payload = {"collections": batch_ids}
        logger.info(f"Checking IDs: {batch_ids}")
        
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=10)
            print(f"DEBUG BATCH {i}: Status {r.status_code} | Text: {r.text[:200]}")
            
            if r.status_code == 200:
                data = r.json()
                if not data:
                    continue
                    
                for char in data:
                    # Parse based on observed structure: {"id":..., "stickerCollectionId":40, "name":...}
                    st_set_id = char.get('stickerCollectionId')
                    # 'name' here seems to be the item name, but maybe we can group by ID?
                    # Or maybe the endpoint returns Collections if we ask for collections?
                    # The endpoint is .../sticker-sets/characters.
                    # Wait, if `name` is "Nyan Cat Party Pack", that sounds like a collection name?
                    # But "Nyan Cat Party Pack" was in the Text snippet.
                    # Let's save whatever name we find associated with the ID.
                    
                    st_name = char.get('name', 'Unknown')
                    
                    if st_set_id:
                         # Store the first name we find for this ID, or append?
                         # Let's just store it.
                        if st_set_id not in all_collections:
                            all_collections[st_set_id] = st_name
                            logger.info(f"FOUND COLLECTION: ID {st_set_id} = {st_name}")
                        else:
                            # If we already have it, maybe check if the name is different (implied collection name vs item name)
                            pass

        except Exception as e:
            logger.error(f"Error checking batch {batch_ids}: {e}")
            
    # Print summary
    print("\n=== DISCOVERED COLLECTIONS ===")
    for cid in sorted(all_collections.keys()):
        print(f"ID {cid}: {all_collections[cid]}")

if __name__ == "__main__":
    discover_collections()
