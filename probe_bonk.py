import requests
import uuid

# BONK: The Dog IDs from previous grep
# FOUND: ('babaa07e-7977-4b77-8c3b-5544710156d6', '71694f56-628d-4235-8664-5006b51c8a4d', 'bonk', 'bonk_the_dog')
COL_ID = "babaa07e-7977-4b77-8c3b-5544710156d6"
CHAR_ID = "71694f56-628d-4235-8664-5006b51c8a4d"

BASE_URLS = [
    "https://storage.googleapis.com/goodies-api-prod.firebasestorage.app/images/collection/",
    "https://storage.googleapis.com/goodies-api-prod.firebasestorage.app/images/sticker/",
    "https://storage.googleapis.com/goodies-api-prod.firebasestorage.app/images/gift/",
    "https://storage.googleapis.com/goodies-api-prod.firebasestorage.app/images/item/",
    "https://storage.googleapis.com/goodies-api-prod.firebasestorage.app/images/"
]

PATTERNS = [
    CHAR_ID,
    f"{CHAR_ID}_1.webp",
    f"{CHAR_ID}/1.webp",
    f"{COL_ID}/{CHAR_ID}",
    f"{COL_ID}/{CHAR_ID}/1.webp",
    # Try case variations?
]

print(f"Probing for BONK assets using IDs:\nCol: {COL_ID}\nChar: {CHAR_ID}\n")

found = False
for base in BASE_URLS:
    for pattern in PATTERNS:
        url = f"{base}{pattern}"
        try:
            r = requests.head(url, timeout=3)
            # 403 or 200 means it exists (403 usually means bucket access perms but file is there, 200 is gold)
            print(f"[{r.status_code}] {url}")
            if r.status_code == 200:
                print(f"✅ FOUND: {url}")
                found = True
                break
        except Exception as e:
            print(f"[ERR] {url}: {e}")
    if found: break

if not found:
    print("❌ No valid URL found in probe.")
