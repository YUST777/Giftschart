#!/usr/bin/env python3
import os
import requests
import logging
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

STICKER_COLLECTIONS_DIR = "/root/01studio/giftschart/sticker_collections"
BASE_URL = "https://storage.googleapis.com/goodies-api-prod.firebasestorage.app/images/collection/"

# Mapping of missing Goodies
# (Collection ID, Sticker/Char ID, Collection Norm, Sticker Norm)
GOODIES_UUID_MAPPING = [
    ("29e48275-fe6b-4701-982f-82782e3db7ae", "77af5944-b475-4e55-bb6e-3482d2a7429e", "teddie", "teddie_nakamoto"),
    ("29e48275-fe6b-4701-982f-82782e3db7ae", "ad6f4c75-2080-4df5-b065-032bf822b648", "teddie", "teddie_xmas"),
    ("29e48275-fe6b-4701-982f-82782e3db7ae", "e672596d-83d3-482f-8b71-ccec5449e8d1", "teddie", "teddie_goodies_intern"),
    ("86a5350c-c671-414d-ae2d-ede3a51a0c9f", "0849b79e-02a1-4cb2-9cab-312bc6523aec", "oracle_red_bull_racing", "boxie_feels"),
    ("86a5350c-c671-414d-ae2d-ede3a51a0c9f", "34f3ec2e-f729-4fcb-adbd-b183324a5b06", "oracle_red_bull_racing", "boxie_pitwall"),
    ("86a5350c-c671-414d-ae2d-ede3a51a0c9f", "d9855f78-83cf-4686-b63d-8e0146f2556a", "oracle_red_bull_racing", "boxie_racer"),
    ("7a372d1a-dc74-43c5-a46b-f34c34dd24f3", "8eced75", "not_wise", "not_wise_stonks_x_goodies"), # Check this ID separately if fails
    ("e0af0188-6876-432d-b328-9240c5105838", "ac399476-012e-4023-bcf6-23e67b0905e3", "wsb", "paper_hands"),
    ("e0af0188-6876-432d-b328-9240c5105838", "aeef7f23-a4d1-47cc-be70-9e9a124ded0c", "wsb", "diamond_hands"),
    ("7803b3f7-21a8-4987-8aa9-7bd59eb39473", "a1125270-2216-43d2-a720-337b5870f033", "cool_cats", "cool_cat_react_pack_i"),
    ("7803b3f7-21a8-4987-8aa9-7bd59eb39473", "2c4ec7d0-0fca-4488-8422-777e8ca1f9da", "cool_cats", "cool_cat_react_pack_ii"),
    ("7f0be678-9580-4aef-bc86-8e02f4e2b844", "990884fb-051b-40e0-9d45-9dfbb78093b5", "doodles", "doodles_timeless_monsters"),
    ("7f0be678-9580-4aef-bc86-8e02f4e2b844", "d5e8a39f-02d8-4885-8492-55c26788b386", "doodles", "doodles_icons_awaken"),
    ("a2d60d85-1b5b-4824-b9b6-3c891ecaf199", "266aa948-8ab4-4cd6-8722-8ea4df05637b", "moonbirds", "moonbirds_set_2_sketch"),
    ("a2d60d85-1b5b-4824-b9b6-3c891ecaf199", "2715e171-d2e9-433a-91a5-b0143581f95a", "moonbirds", "moonbirds_set_2"),
    ("72482696-dc67-461e-99a3-3a759510726d", "15f9c192-1c74-4250-be1d-1fbafadd1de4", "pudgy_penguins_x_kung_fu_panda", "grand_master_oogway"),
    ("72482696-dc67-461e-99a3-3a759510726d", "56d6562f-ddf5-45a3-8df7-d2f3c186b2e0", "pudgy_penguins_x_kung_fu_panda", "dragon_warrior_po"),
    ("72482696-dc67-461e-99a3-3a759510726d", "9e162e31-c406-4b47-ad52-819b0476d1a9", "pudgy_penguins_x_kung_fu_panda", "master_shifu"),
    ("41ad386c-30b3-48a1-99c7-1a45b053cb18", "14bf83c1-1d30-41d2-97ff-38768fcbbfd2", "lamborghini", "lamborghini_revuelto"),
    ("41ad386c-30b3-48a1-99c7-1a45b053cb18", "68b69bcc-8cb2-4f75-87b5-086124ddc9f0", "lamborghini", "lamborghini_urus"),
    ("41ad386c-30b3-48a1-99c7-1a45b053cb18", "b43489ad-00f6-4351-8942-402d7912fb16", "lamborghini", "lamborghini_temerario"),
]

def download_asset(char_id, save_path):
    url = f"{BASE_URL}{char_id}"
    try:
        logger.info(f"Downloading {url}...")
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            # Load as image and convert to WebP
            img = Image.open(io.BytesIO(r.content))
            img.save(save_path, 'WEBP', quality=95)
            logger.info(f"Saved to {save_path}")
            return True
        else:
            logger.error(f"Failed {r.status_code} for {char_id}")
            return False
    except Exception as e:
        logger.error(f"Error downloading {char_id}: {e}")
        return False

def main():
    success = 0
    fail = 0

    for col_uuid, char_id, coll_norm, sticker_norm in GOODIES_UUID_MAPPING:
        # Create directories
        sticker_dir = os.path.join(STICKER_COLLECTIONS_DIR, coll_norm, sticker_norm)
        os.makedirs(sticker_dir, exist_ok=True)
        dest_path = os.path.join(sticker_dir, "1.webp")
        
        # Always overwrite or check if placeholder?
        # Let's overwrite to ensure we get real assets replacing placeholders
        if download_asset(char_id, dest_path):
            success += 1
        else:
            fail += 1
        
    logger.info(f"DONE. Success: {success}, Fail: {fail}")

if __name__ == "__main__":
    main()
