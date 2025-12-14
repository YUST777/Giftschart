import os
import requests
import logging
from typing import Optional
import time

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Catbox.moe API URL
CATBOX_API_URL = "https://catbox.moe/user/api.php"

# In-memory cache to store uploaded image URLs and avoid duplicate uploads
# Format: {gift_name: {"url": url, "timestamp": timestamp}}
CACHE = {}
CACHE_EXPIRY = 3600  # Cache expiry in seconds (1 hour)

def upload_image_to_catbox(image_path: str) -> Optional[str]:
    """
    Upload an image to Catbox.moe and return its URL.
    
    Args:
        image_path: Path to the image file to upload
        
    Returns:
        URL of the uploaded image, or None if upload failed
    """
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
            
        # Prepare the file for upload
        with open(image_path, 'rb') as file:
            files = {'fileToUpload': (os.path.basename(image_path), file, 'image/png')}
            data = {'reqtype': 'fileupload', 'userhash': ''}
            
            # Make API request
            response = requests.post(CATBOX_API_URL, files=files, data=data)
            
            # Check if request was successful
            if response.status_code == 200:
                # The response should be a direct URL to the image
                image_url = response.text.strip()
                if image_url.startswith('https://'):
                    logger.info(f"Image uploaded successfully: {image_url}")
                    return image_url
                else:
                    logger.error(f"API error: {image_url}")
            else:
                logger.error(f"Request failed with status code {response.status_code}")
                logger.error(f"Response: {response.text}")
                
            return None
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        return None
        
def get_gift_card_url(gift_name: str) -> Optional[str]:
    """
    Upload a gift card image to Catbox.moe and return its URL.
    Uses caching to avoid duplicate uploads of the same image.
    
    Args:
        gift_name: Name of the gift
        
    Returns:
        URL of the uploaded gift card image, or None if upload failed
    """
    # Check cache first
    current_time = time.time()
    if gift_name in CACHE:
        cache_entry = CACHE[gift_name]
        # Check if cache entry is still valid
        if current_time - cache_entry["timestamp"] < CACHE_EXPIRY:
            logger.info(f"Using cached URL for {gift_name}: {cache_entry['url']}")
            return cache_entry["url"]
    
    # Normalize gift name for file matching
    if gift_name == "Jack-in-the-Box":
        normalized_name = "Jack_in_the_Box"
    elif gift_name == "Durov's Cap":
        normalized_name = "Durovs_Cap"
    else:
        normalized_name = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
    
    # Gift card file path
    gift_card_path = os.path.join(script_dir, "new_gift_cards", f"{normalized_name}_card.png")
    
    # Check if the gift card exists
    if not os.path.exists(gift_card_path):
        logger.error(f"Gift card not found: {gift_card_path}")
        return None
    
    # Upload the gift card
    url = upload_image_to_catbox(gift_card_path)
    
    # Cache the result if successful
    if url:
        CACHE[gift_name] = {"url": url, "timestamp": current_time}
    
    return url

# Test the module if run directly
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # If a gift name is provided as a command-line argument, upload that gift's card
        gift_name = sys.argv[1]
        print(f"Uploading gift card for: {gift_name}")
        url = get_gift_card_url(gift_name)
        if url:
            print(f"Success! Card URL: {url}")
        else:
            print("Failed to upload gift card.")
    else:
        # Otherwise, list all available gift cards
        print("Available gift cards:")
        from glob import glob
        cards = glob(os.path.join(script_dir, "new_gift_cards", "*_card.png"))
        for card in cards:
            gift_name = os.path.basename(card).replace("_card.png", "")
            print(f"- {gift_name}")
        print("\nUsage: python image_uploader.py <gift_name>")