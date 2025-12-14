#!/usr/bin/env python3
"""
Generate Sticker Price Cards

This script generates sticker price cards using the new templates created by generate_sticker_templates.py
and adds real-time price data from MRKT API.
"""

import os
import sys
import json
import logging
import argparse
from PIL import Image, ImageDraw, ImageFont
import mrkt_api_improved as mrkt_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('generate_sticker_price_card')

# Get script directory for cross-platform compatibility
script_dir = os.path.dirname(os.path.abspath(__file__))

# Constants - use os.path.join for cross-platform compatibility
TEMPLATES_DIR = os.path.join(script_dir, "sticker_templates")
METADATA_DIR = os.path.join(script_dir, "sticker_metadata")
OUTPUT_DIR = os.path.join(script_dir, "Sticker_Price_Cards")
PRICE_DATA_FILE = os.path.join(script_dir, "sticker_price_results.json")
FONT_PATH = os.path.join(script_dir, "Typekiln - EloquiaDisplay-ExtraBold.otf")

# TON to USD conversion rate
# Import TON price utility
try:
    from ton_price_utils import get_ton_price_usd
except ImportError:
    def get_ton_price_usd():
        return 2.10  # Fallback value

def normalize_filename(name):
    """Normalize filename for file operations"""
    # Special case for collections with '&' in their name
    if name == "Pudgy & Friends":
        return "Pudgy_and_Friends"
    elif name == "Lazy & Rich":
        return "Lazy_and_Rich"
    # Special case for specific stickers with "Friends" in their name
    elif name == "Pudgy and Friends Friends Pengu x NASCAR":
        return "Pudgy_and_Friends_Pengu_x_NASCAR"
    elif name == "Pudgy and Friends Friends Pengu x Baby Shark":
        return "Pudgy_and_Friends_Pengu_x_Baby_Shark"
    # Special case for Lazy and Rich stickers
    elif name == "Lazy and Rich Rich Sloth Capital":
        return "Lazy_and_Rich_Sloth_Capital"
    elif name == "Lazy and Rich Rich Chill or thrill":
        return "Lazy_and_Rich_Chill_or_thrill"
    else:
        return name.replace(' ', '_').replace('&', '_and_')

def load_price_data():
    """Load price data from JSON file or fetch from MRKT API if needed"""
    try:
        # First try to load from existing file
        if os.path.exists(PRICE_DATA_FILE):
            with open(PRICE_DATA_FILE, 'r') as f:
                data = json.load(f)
                # Check if data is valid
                if 'stickers_with_prices' in data and data['stickers_with_prices']:
                    logger.info(f"Loaded price data from {PRICE_DATA_FILE}")
                    return data
        
        # If file doesn't exist or is invalid, fetch fresh data
        logger.info("Fetching fresh price data from MRKT API")
        
        # Initialize result structure
        result = {
            "timestamp": None,
            "total_templates": 0,
            "successful": 0,
            "failed": 0,
            "stickers_with_prices": []
        }
        
        # Get all template files
        templates = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith('_template.png')]
        result['total_templates'] = len(templates)
        
        # Process each template
        for template_file in templates:
            # Extract collection and sticker name from template filename
            try:
                parts = template_file.replace('_template.png', '').split('_')
                
                # Handle complex names
                if len(parts) <= 1:
                    continue
                    
                # Try to identify collection and sticker
                if parts[0] in ["Pudgy", "Lazy", "Dogs", "Not", "Flappy", "Bored", "Ric"]:
                    # Special case handling for complex collection names
                    if parts[0] == "Pudgy" and parts[1] == "and":
                        collection = "Pudgy and Friends"
                        sticker = " ".join(parts[2:])
                    elif parts[0] == "Lazy" and parts[1] == "and":
                        collection = "Lazy and Rich"
                        sticker = " ".join(parts[2:])
                    elif parts[0] == "Dogs" and parts[1] == "OG":
                        collection = "Dogs OG"
                        sticker = " ".join(parts[2:])
                    elif parts[0] == "Bored" and parts[1] == "Stickers":
                        collection = "Bored Stickers"
                        sticker = " ".join(parts[2:])
                    elif parts[0] == "Not" and parts[1] == "Pixel":
                        collection = "Not Pixel"
                        sticker = " ".join(parts[2:])
                    elif parts[0] == "Flappy" and parts[1] == "Bird":
                        collection = "Flappy Bird"
                        sticker = " ".join(parts[2:])
                    elif parts[0] == "Ric" and parts[1] == "Flair":
                        collection = "Ric Flair"
                        sticker = " ".join(parts[2:])
                    else:
                        collection = parts[0]
                        sticker = " ".join(parts[1:])
                else:
                    # Standard case
                    collection = parts[0]
                    sticker = " ".join(parts[1:])
                
                # Get price from MRKT API
                search_term = f"{collection} {sticker}"
                price_data = mrkt_api.get_sticker_price(search_term)
                
                if price_data and 'price' in price_data and price_data['price'] > 0:
                    # Add to result
                    result['stickers_with_prices'].append({
                        "collection": collection,
                        "sticker": sticker,
                        "price": price_data['price'],
                        "is_real_data": not price_data.get('is_mock_data', True)
                    })
                    result['successful'] += 1
                else:
                    # Add with zero price
                    result['stickers_with_prices'].append({
                        "collection": collection,
                        "sticker": sticker,
                        "price": 0,
                        "is_real_data": False
                    })
                    result['failed'] += 1
            except Exception as e:
                logger.error(f"Error processing template {template_file}: {e}")
                result['failed'] += 1
        
        # Save the result
        with open(PRICE_DATA_FILE, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
    except Exception as e:
        logger.error(f"Error loading price data: {e}")
        return None

def load_metadata(collection, sticker):
    """Load metadata for a specific sticker"""
    try:
        # Normalize names
        collection_norm = normalize_filename(collection)
        sticker_norm = normalize_filename(sticker)
        
        # Metadata path
        metadata_path = os.path.join(METADATA_DIR, f"{collection_norm}_{sticker_norm}_metadata.json")
        
        # Check if metadata exists
        if not os.path.exists(metadata_path):
            logger.warning(f"Metadata not found: {metadata_path}")
            return None
        
        # Load metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return metadata
    except Exception as e:
        logger.error(f"Error loading metadata for {collection} - {sticker}: {e}")
        return None

def generate_price_card(collection, sticker, price, output_dir):
    """Generate a price card for a sticker using the template and metadata, or a fallback if missing."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        collection_norm = normalize_filename(collection)
        sticker_norm = normalize_filename(sticker)
        template_path = os.path.join(TEMPLATES_DIR, f"{collection_norm}_{sticker_norm}_template.png")
        # Try to load template, else fallback
        if os.path.exists(template_path):
        template = Image.open(template_path).convert("RGBA")
        draw = ImageDraw.Draw(template)
        
        # Get dominant color from the metadata
            dominant_color = tuple(load_metadata(collection, sticker).get('dominant_color', (148, 68, 143)))
        
        # Calculate USD price
        ton_price_usd = get_ton_price_usd()
        price_usd = price * ton_price_usd
        
        # Calculate price in Telegram Stars (1 Star = $0.016)
        stars_price = int(price_usd / 0.016)
        
        # Load fonts
        try:
            price_font = ImageFont.truetype(FONT_PATH, 140)  # For USD price
            ton_price_font = ImageFont.truetype(FONT_PATH, 50)  # For TON and Star prices
        except Exception as e:
            logger.error(f"Error loading font: {e}")
            # Fallback to default font
            price_font = ImageFont.load_default()
            ton_price_font = ImageFont.load_default()
        
        # Get positions from metadata
            dollar_x = load_metadata(collection, sticker).get('dollar_x', 155)
            dollar_y = load_metadata(collection, sticker).get('dollar_y', 285)
            ton_x = load_metadata(collection, sticker).get('ton_x', 215)
            ton_y = load_metadata(collection, sticker).get('ton_y', 465)
            star_x = load_metadata(collection, sticker).get('star_x', 515)
            star_y = load_metadata(collection, sticker).get('star_y', 465)
        
        # Draw dollar sign with the dominant color
        dollar_color = dominant_color
        price_color = (20, 20, 20)  # Almost black
        draw.text((dollar_x, dollar_y), "$", fill=dollar_color, font=price_font)
        
        # Draw USD price
        draw.text((dollar_x + 100, dollar_y), f"{price_usd:,.0f}".replace(",", " "), fill=price_color, font=price_font)
        
        # Draw TON price text
        draw.text((ton_x, ton_y), f"{price:.1f}".replace(".", ",").replace(",0", ""), fill=price_color, font=ton_price_font)
        
        # Draw Star price text
        draw.text((star_x, star_y), f"{stars_price:,}".replace(",", " "), fill=price_color, font=ton_price_font)
        
        # Save the card
        output_filename = f"{collection_norm}_{sticker_norm}_price_card.png"
        output_path = os.path.join(output_dir, output_filename)
        template.save(output_path)
        logger.info(f"Generated price card: {output_path}")
        return output_path
        else:
            # Fallback: create a generic card
            logger.warning(f"Template not found: {template_path}, using fallback design.")
            from PIL import ImageFont
            card = Image.new('RGBA', (1600, 1000), (148, 68, 143, 255))
            draw = ImageDraw.Draw(card)
            try:
                font = ImageFont.truetype(FONT_PATH, 80)
            except Exception:
                font = ImageFont.load_default()
            draw.text((100, 100), f"{collection}", fill=(255,255,255), font=font)
            draw.text((100, 250), f"{sticker}", fill=(255,255,255), font=font)
            draw.text((100, 400), f"Price: {price} TON", fill=(255,255,0), font=font)
            output_filename = f"{collection_norm}_{sticker_norm}_price_card.png"
            output_path = os.path.join(output_dir, output_filename)
            card.save(output_path)
            logger.info(f"Generated fallback price card: {output_path}")
            return output_path
    except Exception as e:
        logger.error(f"Error generating price card for {collection} - {sticker}: {e}")
        return None

def generate_all_price_cards(price_data, output_dir):
    """Generate price cards for all stickers with prices"""
    if not price_data or 'stickers_with_prices' not in price_data:
        logger.error("Invalid price data")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Track results
    successful = 0
    failed = 0
    
    # Generate cards for each sticker with price
    for item in price_data['stickers_with_prices']:
        collection = item['collection']
        sticker = item['sticker']
        price = item['price']
        
        logger.info(f"Generating price card for {collection} - {sticker}: {price} TON")
        result = generate_price_card(collection, sticker, price, output_dir)
        
        if result:
            successful += 1
        else:
            failed += 1
    
    logger.info(f"Price card generation complete: {successful} successful, {failed} failed")
    return successful, failed

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate sticker price cards")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory for generated cards")
    parser.add_argument("--collection", help="Generate card for specific collection")
    parser.add_argument("--sticker", help="Generate card for specific sticker")
    parser.add_argument("--refresh", action="store_true", help="Refresh price data from MRKT API")
    
    args = parser.parse_args()
    
    # Delete price data file if refresh requested
    if args.refresh and os.path.exists(PRICE_DATA_FILE):
        os.remove(PRICE_DATA_FILE)
        logger.info(f"Deleted {PRICE_DATA_FILE} for refresh")
    
    # Load price data
    price_data = load_price_data()
    if not price_data:
        logger.error("Failed to load price data")
        sys.exit(1)
    
    # Generate cards
    if args.collection and args.sticker:
        # Generate single card
        price = None
        for item in price_data['stickers_with_prices']:
            if item['collection'] == args.collection and item['sticker'] == args.sticker:
                price = item['price']
                break
                
        if price is not None:
            generate_price_card(args.collection, args.sticker, price, args.output_dir)
        else:
            # Try to fetch price from API directly
            search_term = f"{args.collection} {args.sticker}"
            price_data = mrkt_api.get_sticker_price(search_term)
            
            if price_data and 'price' in price_data:
                generate_price_card(args.collection, args.sticker, price_data['price'], args.output_dir)
            else:
                logger.warning(f"No price found for {args.collection} - {args.sticker}, using mock price")
                # Use mock price for demonstration
                mock_price = 118.25  # Example from the screenshot for Pudgy and Friends Pengu x NASCAR
                generate_price_card(args.collection, args.sticker, mock_price, args.output_dir)
    else:
        # Generate all cards
        generate_all_price_cards(price_data, args.output_dir)

if __name__ == "__main__":
    main() 