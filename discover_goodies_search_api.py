import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token from previous context
TOKEN = "9a9d7375-55da-45e3-a886-65cd197812bb"
BASE_URL = "https://api.tgmrkt.io/api/v1"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def probe_endpoint(endpoint, query):
    url = f"{BASE_URL}{endpoint}"
    params = {"q": query}
    try:
        logger.info(f"Querying {url} with q={query}...")
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        
        logger.info(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            # Save raw response for inspection
            filename = f"search_response_{endpoint.replace('/', '_')}_{query}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved response to {filename}")
            
            # Quick check for image fields
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get('results', []) or data.get('items', []) or [data]
            else:
                items = []

            for item in items[:3]: # check first few
                logger.info(f"Item: {json.dumps(item)[:200]}...")

        else:
            logger.error(f"Failed with {response.status_code}: {response.text}")

    except Exception as e:
        logger.error(f"Error probing {endpoint}: {e}")

def main():
    # Try different search endpoints
    endpoints = [
        "/gifts/search",
        "/stickers/search",
        "/collections/search",
        "/catalog/search"
    ]
    
    queries = ["Teddie", "Lamborghini", "Doodles"]

    for endp in endpoints:
        for q in queries:
            probe_endpoint(endp, q)

if __name__ == "__main__":
    main()
