import os
import requests
import sys
import json
import time
import logging
from difflib import get_close_matches

# Set up logging for main.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("main")

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Complete updated list of gift names
names = [
    "Heart Locket", "Lush Bouquet", "Astral Shard", "B-Day Candle", "Berry Box",
    "Big Year", "Bonded Ring", "Bow Tie", "Bunny Muffin", "Candy Cane",
    "Cookie Heart", "Crystal Ball", "Desk Calendar", "Diamond Ring", "Durov's Cap",
    "Easter Egg", "Electric Skull", "Eternal Candle", "Eternal Rose", "Evil Eye",
    "Flying Broom", "Gem Signet", "Genie Lamp", "Ginger Cookie", "Hanging Star",
    "Heroic Helmet", "Hex Pot", "Holiday Drink", "Homemade Cake", "Hypno Lollipop",
    "Ion Gem", "Jack-in-the-Box", "Jelly Bunny", "Jester Hat", "Jingle Bells",
    "Kissed Frog", "Light Sword", "Lol Pop", "Loot Bag", "Love Candle",
    "Low Rider", "Love Potion", "Lunar Snake", "Mad Pumpkin", "Magic Potion", "Mini Oscar",
    "Nail Bracelet", "Neko Helmet", "Party Sparkler", "Perfume Bottle", "Pet Snake",
    "Plush Pepe", "Precious Peach", "Record Player", "Restless Jar", "Sakura Flower",
    "Santa Hat", "Scared Cat", "Sharp Tongue", "Signet Ring", "Skull Flower",
    "Sleigh Bell", "Snake Box", "Snow Globe", "Snow Mittens", "Snoop Cigar", "Snoop Dogg",
    "Spiced Wine", "Spy Agaric", "Star Notepad", "Swag Bag", "Swiss Watch", "Tama Gadget", "Top Hat",
    "Toy Bear", "Trapped Heart", "Vintage Cigar", "Voodoo Doll", "Westside Sign", "Winter Wreath",
    "Witch Hat", "Xmas Stocking", 
    # Premarket gifts (newer releases)
    "Cupid Charm", "Whip Cupcake", "Joyful Bundle", "Valentine Box",
    # New premarket gifts (2024 releases)
    "Clover Pin", "Fresh Socks", "Sky Stilettos", "Artisan Brick", "Mighty Arm", "Input Key",
    # New premarket gifts (2025 releases)
    "Happy Brownie", "Spring Basket", "Instant Ramen", "Faith Amulet", "Mousse Cake", "Ice Cream",
    # Premarket gifts (2025 November releases) - use Tonnel API
    "Bling Binky", "Money Pot", "Pretty Posy",
    # Now regular market gifts (moved from premarket)
    "Ionic Dryer", "Moon Pendant", "Jolly Chimp", "Stellar Rocket",
    # Plus premarket gifts (+premarket category) - 30 gifts from MRKT/Quant marketplaces
    "1 May", "Backpack", "Bird Mark", "Book", "Case", "Coconut Drink", "Coffin",
    "Cone IceCream", "Cream IceCream", "Durov Glasses", "Durov's Statuette", "Eagle",
    "Easter Cake", "Eight Roses", "Golden Medal", "Grave", "Heart Pendant", "Lamp Candle",
    "Mask", "Pencil", "Pink Flamingo", "REDO", "Red Star", "Sand Castle", "Sneakers",
    "Statue", "Surfboard", "T-shirt", "Torch", "Airplane"
]

base_url = "https://cdn.changes.tg/gifts/models/{}/png/Original.png"

# Create output folder
output_folder = os.path.join(script_dir, "downloaded_images")
os.makedirs(output_folder, exist_ok=True)

# Special URLs that need special handling
special_urls = {
    "Jack-in-the-Box": "https://cdn.changes.tg/gifts/models/Jack-in-the-Box/png/Original.png",
    "B-Day Candle": "https://cdn.changes.tg/gifts/models/B-Day%20Candle/png/Original.png",
    "Durov's Cap": "https://cdn.changes.tg/gifts/models/Durov's%20Cap/png/Original.png",
    "Plush Pepe": "https://cdn.changes.tg/gifts/models/Plush%20Pepe/png/Original.png",
    "Perfume Bottle": "https://cdn.changes.tg/gifts/models/Perfume%20Bottle/png/Original.png",
    "Precious Peach": "https://cdn.changes.tg/gifts/models/Precious%20Peach/png/Original.png"
}

def download_image(url, filepath, name):
    """Download a single image with retries"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            logger.info(f"Downloaded: {os.path.basename(filepath)}")
            return True
        except requests.RequestException as e:
            logger.error(f"Attempt {attempt+1}/{max_retries} failed for {name}: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Failed to download {name} after {max_retries} attempts")
                return False

# Check if we should skip downloads because templates already exist
templates_folder = os.path.join(script_dir, "card_templates")
templates_exist = os.path.exists(templates_folder) and len(os.listdir(templates_folder)) > 50

if templates_exist:
    print("Templates already exist, skipping image downloads")
else:
    # First try the special URLs that we know work
    for name, url in special_urls.items():
        # Normalize the filename for consistency
        safe_name = name.replace(' ', '_').replace('-', '_').replace("'", '')
        filename = f"{safe_name}.png"
        filepath = os.path.join(output_folder, filename)
        
        # Skip if file already exists
        if os.path.exists(filepath):
            print(f"Already exists: {filename}")
            continue
            
        download_image(url, filepath, name)

    # Then try to download all the items from the list
    for name in names:
        # Skip items that are in special_URLs as they've already been downloaded
        if name in special_urls:
            continue
            
        # Normalize the filename for consistency
        safe_name = name.replace(' ', '_').replace('-', '_').replace("'", '')
        filename = f"{safe_name}.png"
        filepath = os.path.join(output_folder, filename)
        
        # Skip if file already exists
        if os.path.exists(filepath):
            print(f"Already exists: {filename}")
            continue
            
        # Replace spaces with %20, handle other special characters
        url_name = name.replace(' ', '%20').replace("'", '%27')
        url = base_url.format(url_name)
        download_image(url, filepath, name)

print("Gift image check complete")

# Load simplified gift names
def load_simplified_names():
    names = {}
    downloads_dir = os.path.join(script_dir, "downloaded_images")
    if not os.path.exists(downloads_dir):
        logger.warning(f"Downloads directory not found: {downloads_dir}")
        os.makedirs(downloads_dir, exist_ok=True)
        return names
        
    try:
        gift_files = [f for f in os.listdir(downloads_dir) if f.endswith(".png")]
        for filename in gift_files:
            gift_name = os.path.splitext(filename)[0].replace("_", " ")
            simplified = gift_name.lower().replace("-", " ").replace("'", "")
            names[simplified] = gift_name
    except Exception as e:
        logger.error(f"Error loading simplified names: {e}")
    return names

# Define global variable for simplified names to be used in find_matching_gifts
simplified_names = load_simplified_names()
globals()["simplified_names"] = simplified_names

def test_gift_groups():
    """Test the gift group functionality"""
    print("\nTesting Gift Groups:")
    
    # Import locally to avoid circular import
    try:
        from telegram_bot import find_matching_gifts
        groups = ["ring", "hat", "heart", "candle", "snake", "box", "bunny", "signet", "potion", "bell"]
        
        for group in groups:
            results = find_matching_gifts(group)
            print(f"\nSearch for '{group}':")
            if results:
                for i, gift in enumerate(results, 1):
                    print(f"  {i}. {gift}")
            else:
                print("  No results found")
    except ImportError:
        print("  Cannot test gift groups - telegram_bot not available")

def test_exclusion_rule():
    """Test that 'ton' doesn't match anything"""
    print("\nTesting Exclusion Rule:")
    try:
        from telegram_bot import find_matching_gifts
        results = find_matching_gifts("ton")
        if not results:
            print("  ✅ 'ton' correctly returns no matches")
        else:
            print("  ❌ 'ton' incorrectly matched:", results)
    except ImportError:
        print("  Cannot test exclusion rule - telegram_bot not available")

def test_specific_matching():
    """Test specific gift matching"""
    print("\nTesting Specific Gift Matching:")
    
    try:
        from telegram_bot import find_matching_gifts
        test_cases = [
            "diamond ring",
            "witch",
            "snake",
            "tama gadget",
            "top hat",
            "heart"
        ]
        
        for query in test_cases:
            results = find_matching_gifts(query)
            print(f"\nSearch for '{query}':")
            if results:
                for i, gift in enumerate(results, 1):
                    print(f"  {i}. {gift}")
            else:
                print("  No results found")
    except ImportError:
        print("  Cannot test specific matching - telegram_bot not available")

def main():
    """Main test function"""
    print("Gift Matching Test")
    print("-----------------")
    
    # Run the tests
    test_gift_groups()
    test_exclusion_rule()
    test_specific_matching()
    
    print("\nTesting complete!")

if __name__ == "__main__":
    main()
