#!/usr/bin/env python3
"""
Live Price Card Generator

This script generates a price card for a sticker using live data from the MRKT API.
It bypasses the cached supply data and fetches real-time price information.
"""

import os
import sys
import json
import logging
import argparse
import mrkt_api_improved

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("live_price_card")

# Get script directory for cross-platform compatibility
script_dir = os.path.dirname(os.path.abspath(__file__))

# Constants - use os.path.join for cross-platform compatibility
OUTPUT_DIR = os.path.join(script_dir, "Sticker_Price_Cards")

def normalize_filename(name):
    """Normalize filename for file operations"""
    # Special case for collections with '&' in their name
    if name == "Pudgy & Friends":
        return "Pudgy_and_Friends"
    elif name == "Lazy & Rich":
        return "Lazy_and_Rich"
    else:
        return name.replace(' ', '_').replace('&', 'AND')

def generate_live_price_card(collection, sticker):
    """Generate a price card using live data from the MRKT API"""
    # Clear API cache to ensure fresh data
    mrkt_api_improved.clear_cache()
    logger.info(f"Generating live price card for {collection} - {sticker}")
    
    # Get live price data
    search_term = f"{collection} {sticker}"
    price_data = mrkt_api_improved.get_sticker_price(search_term, use_cache=False)
    
    if not price_data or "price" not in price_data:
        logger.error(f"Failed to get price data for {search_term}")
        print(f"❌ ERROR: Could not get live price data for {collection} - {sticker}")
        return False
    
    price = price_data["price"]
    print(f"🌐 LIVE API: Got fresh price data for {collection} - {sticker}: {price} TON")
    
    # Import the card generator directly to avoid circular imports
    import importlib.util
    card_generator_path = os.path.join(script_dir, "sticker_price_card_generator.py")
    spec = importlib.util.spec_from_file_location("card_generator", card_generator_path)
    card_generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(card_generator)
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generate the card using the imported module
    collection_norm = normalize_filename(collection)
    sticker_norm = normalize_filename(sticker)
    
    # Find sticker image
    sticker_image_path = None
    sticker_collections_dir = os.path.join(script_dir, "sticker_collections")
    for root, dirs, files in os.walk(sticker_collections_dir):
        for directory in dirs:
            if directory.lower() == sticker_norm.lower():
                sticker_dir = os.path.join(root, directory)
                for file in os.listdir(sticker_dir):
                    if file.endswith('.png') or file.endswith('.jpg'):
                        sticker_image_path = os.path.join(sticker_dir, file)
                        break
                if sticker_image_path:
                    break
        if sticker_image_path:
            break
    
    if not sticker_image_path:
        print(f"⚠️ WARNING: Could not find sticker image for {collection} - {sticker}")
        # Try to find a template
        template_path = None
        template_name = f"{collection_norm}_{sticker_norm}_template.png"
        sticker_templates_dir = os.path.join(script_dir, "sticker_templates")
        if os.path.exists(os.path.join(sticker_templates_dir, template_name)):
            template_path = os.path.join(sticker_templates_dir, template_name)
        
        if not template_path:
            print(f"❌ ERROR: Could not find template for {collection} - {sticker}")
            return False
    
    # Generate the card
    try:
        # Create a basic card with the price
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a new image
        card_width = 1600
        card_height = 1000
        card = Image.new('RGBA', (card_width, card_height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(card)
        
        # Draw collection and sticker names
        font_path = os.path.join(script_dir, "Typekiln - EloquiaDisplay-ExtraBold.otf")
        try:
            font = ImageFont.truetype(font_path, 60)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 50), f"Collection: {collection}", fill=(0, 0, 0), font=font)
        draw.text((50, 150), f"Sticker: {sticker}", fill=(0, 0, 0), font=font)
        draw.text((50, 250), f"Price: {price} TON", fill=(0, 0, 0), font=font)
        draw.text((50, 350), "LIVE PRICE DATA", fill=(255, 0, 0), font=font)
        
        # Save the card
        output_filename = f"{collection_norm}_{sticker_norm}_live_price_card.png"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        card.save(output_path)
        
        print(f"✅ Successfully generated live price card: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error generating card: {e}")
        print(f"❌ ERROR: Failed to generate card: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate a price card using live data from the MRKT API")
    parser.add_argument("--collection", required=True, help="Sticker collection name")
    parser.add_argument("--sticker", required=True, help="Sticker name")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory for generated cards")
    
    args = parser.parse_args()
    
    # Generate the card
    generate_live_price_card(args.collection, args.sticker)

if __name__ == "__main__":
    main() 