
import os
import requests
import shutil

# Target directory
DOWNLOAD_DIR = "/root/01studio/giftschart/downloaded_images"

# Items to download
# (filename_base, cdn_key)
ITEMS = [
    ("Khabib's_Papakha", "gifts/stickers/thumbnails/4b6861626962e280997320506170616b68615f486f6e6f72.webp"),
    ("UFC_Strike", "gifts/stickers/thumbnails/55464320537472696b655f4d2e204476616c69736876696c69.webp"),
    # Try fetching the other Khabib key just in case (as temp)
    ("Khabib_Star", "stars_gifts/stickers/thumbnails/5839094187366024301.webp")
]

BASE_URLS = [
    "https://cdn.tgmrkt.io",
    "https://cache.tgmrkt.io",
    "https://api.tgmrkt.io/cdn", 
    "https://nft.fragment.com" # Just in case
]

def download_image(name, key):
    final_path = os.path.join(DOWNLOAD_DIR, f"{name}.webp")
    
    for base in BASE_URLS:
        url = f"{base}/{key}"
        try:
            print(f"Trying {url}...")
            r = requests.get(url, stream=True, timeout=5)
            if r.status_code == 200:
                with open(final_path, 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
                print(f"✅ Success: Saved {final_path}")
                return True
        except Exception as e:
            print(f"Error {base}: {e}")
            
    print(f"❌ Failed to download {name}")
    return False

def main():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        
    for name, key in ITEMS:
        download_image(name, key)

if __name__ == "__main__":
    main()
