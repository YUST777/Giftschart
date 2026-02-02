import requests
import time

USER_TOKEN = "9a9d7375-55da-45e3-a886-65cd197812bb"
HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {USER_TOKEN}"
}

MISSING_NAMES = [
    "Not Pixel",
    "Bored Ape Yacht Club",
    "CITY Holder",
    "Chimpers Dojo",
    "DOGS NY",
    "Not_NY.exe"
]

def search_and_print_id(query):
    # Try searching for sticker sets
    # Endpoint might be /api/v1/sticker-sets/characters?search=...
    # Or /api/v1/stickers/collections (listing all and filtering)
    
    # Let's try listing collections first as it's more reliable
    # But we don't know the page.
    # Let's try the search endpoint used in discover_goodies_mrkt.py
    url = f"https://api.tgmrkt.io/api/v1/sticker-sets/characters?search={query}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            # This returns characters, but we want collection IDs probably
            # Let's look at the structure
            results = data.get('results', [])
            for res in results:
                print(f"MATCH: {query} -> {res}")
        else:
            print(f"Failed {r.status_code} for {query}")
    except Exception as e:
        print(f"Error {query}: {e}")

# Alternative: scan collections 150-250?
def scan_collections_range():
    print("Scanning collections 61-300...")
    url = "https://api.tgmrkt.io/api/v1/stickers/collections"
    
    # We can request specific IDs
    chunk_size = 50
    for i in range(61, 301, chunk_size):
        ids = list(range(i, i + chunk_size))
        payload = {"collections": ids}
        try:
            r = requests.post(url, headers=HEADERS, json=payload, timeout=10)
            if r.status_code == 200:
                data = r.json()
                for col in data:
                    c_id = col.get('id')
                    c_name = col.get('name')
                    print(f"COLLECTION: {c_id} - {c_name}")
        except Exception as e:
            print(f"Error chunk {i}: {e}")
        time.sleep(1)

if __name__ == "__main__":
    scan_collections_range()
