import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_TOKEN = "9a9d7375-55da-45e3-a886-65cd197812bb"
URL = "https://api.tgmrkt.io/api/v1/sticker-sets/characters"

# Teddie and Lamborghini Collection UUIDs
COLLECTION_IDS = [
    "29e48275-fe6b-4701-982f-82782e3db7ae", # Teddie
    "41ad386c-30b3-48a1-99c7-1a45b053cb18"  # Lamborghini
]

def test():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {USER_TOKEN}"
    }
    
    payload = {"collections": COLLECTION_IDS}
    
    logger.info(f"Sending payload: {payload}")
    
    try:
        r = requests.post(URL, headers=headers, json=payload, timeout=30)
        logger.info(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(json.dumps(data, indent=2))
        else:
            logger.error(f"Error: {r.text}")
    except Exception as e:
        logger.error(f"Exception: {e}")

if __name__ == "__main__":
    test()
