
from PIL import Image
import os
import sys

files = ["Khabib's_Papakha.png", "UFC_Strike.png"]
img_dir = "/root/01studio/giftschart/downloaded_images"

for f in files:
    path = os.path.join(img_dir, f)
    if os.path.exists(path):
        try:
            print(f"Processing {f}...")
            img = Image.open(path)
            webp_path = path.replace('.png', '.webp')
            img.save(webp_path, "WEBP")
            print(f"Saved {webp_path}")
            os.remove(path)
            print(f"Deleted {path}")
        except Exception as e:
            print(f"Error {f}: {e}")
    else:
        print(f"bit found: {path} (maybe already converted?)")
