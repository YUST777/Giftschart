#!/usr/bin/env python3
"""
Generate Sticker Price Cards

This script generates sticker price cards using the MRKT API prices and existing templates.
It creates visually appealing cards with real-time price information, matching the gift card design.
"""

import os
import sys
import json
import logging
import argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import stickers_tools_api as sticker_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('generate_sticker_price_cards')

# Get script directory for cross-platform compatibility
script_dir = os.path.dirname(os.path.abspath(__file__))

# Constants - use os.path.join for cross-platform compatibility
TEMPLATES_DIR = os.path.join(script_dir, "sticker_templates")
OUTPUT_DIR = os.path.join(script_dir, "Sticker_Price_Cards")
ASSETS_DIR = os.path.join(script_dir, "assets")
PRICE_DATA_FILE = os.path.join(script_dir, "sticker_price_results.json")
TON_LOGO_PATH = os.path.join(ASSETS_DIR, "TON2.png")
STAR_LOGO_PATH = os.path.join(ASSETS_DIR, "star.png")
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
    # Special case for "Pudgy & Friends" which has a template name of "Pudgy_and_Friends"
    if name == "Pudgy & Friends":
        return "Pudgy_and_Friends"
    elif name == "Lazy & Rich":
        return "Lazy_and_Rich"
    else:
        return name.replace(' ', '_').replace('&', 'AND')

def load_price_data():
    """Load price data from the JSON file"""
    try:
        with open(PRICE_DATA_FILE, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error loading price data: {e}")
        return None

def get_sticker_price(price_data, collection, sticker):
    """Get price for a specific sticker from the price data"""
    if not price_data or 'stickers_with_prices' not in price_data:
        return None
        
    for item in price_data['stickers_with_prices']:
        if item['collection'] == collection and item['sticker'] == sticker:
            return item['price']
    
    # If not found, try to get from MRKT API directly
    price_info = sticker_api.get_sticker_price(collection, sticker)
    if price_info:
        return price_info['floor_price_ton']
    
    return None

def get_dominant_color(image_path):
    """Get the dominant color from an image"""
    try:
        img = Image.open(image_path)
        # Convert to RGBA if needed
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create a smaller version for faster processing
        img.thumbnail((100, 100))
        
        # Get color data
        pixels = list(img.getdata())
        
        # Filter out transparent pixels
        pixels = [p for p in pixels if p[3] > 128]
        
        if not pixels:
            return (128, 128, 128)  # Default gray if all pixels are transparent
        
        # Simple average color
        r_sum = sum(p[0] for p in pixels)
        g_sum = sum(p[1] for p in pixels)
        b_sum = sum(p[2] for p in pixels)
        
        count = len(pixels)
        return (r_sum // count, g_sum // count, b_sum // count)
    except Exception as e:
        logger.error(f"Error getting dominant color: {e}")
        return (128, 128, 128)  # Default gray on error

def generate_price_card(collection, sticker, price, output_dir):
    """Generate a price card for a sticker using the template"""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Normalize names for file operations
        collection_norm = normalize_filename(collection)
        sticker_norm = normalize_filename(sticker)
        
        # Template path
        template_path = os.path.join(TEMPLATES_DIR, f"{collection_norm}_{sticker_norm}_template.png")
        
        # Check if template exists
        if not os.path.exists(template_path):
            logger.warning(f"Template not found: {template_path}")
            return None
            
        # Load template image
        template = Image.open(template_path).convert("RGBA")
        
        # Create a drawing context
        draw = ImageDraw.Draw(template)
        
        # Get image dimensions
        width, height = template.size
        
        # Calculate center position for elements (similar to gift card)
        x_center = width // 2 - 800
        y_center = height // 2 - 500
        
        # Get dominant color from the template
        dominant_color = get_dominant_color(template_path)
        
        # Calculate USD price
        ton_price_usd = get_ton_price_usd()
        price_usd = price * ton_price_usd
        
        # Calculate price in Telegram Stars (1 Star = $0.016)
        stars_price = int(price_usd / 0.016)
        
        # Load fonts
        try:
            price_font = ImageFont.truetype(FONT_PATH, 140)
            ton_price_font = ImageFont.truetype(FONT_PATH, 50)
        except Exception as e:
            logger.error(f"Error loading font: {e}")
            # Fallback to default font
            price_font = ImageFont.load_default()
            ton_price_font = ImageFont.load_default()
        
        # Dollar sign and USD price - use exact positions from gift card
        dollar_x = x_center + 180
        dollar_y = y_center + 280
        
        # Draw dollar sign
        dollar_color = dominant_color
        price_color = (20, 20, 20)
        draw.text((dollar_x, dollar_y), "$", fill=dollar_color, font=price_font)
        
        # Draw USD price
        draw.text((dollar_x + 100, dollar_y), f"{price_usd:,.0f}".replace(",", " "), fill=price_color, font=price_font)
        
        # Load and colorize TON logo
        ton_logo = Image.open(TON_LOGO_PATH)
        if ton_logo.mode != 'RGBA':
            ton_logo = ton_logo.convert('RGBA')
        
        # Resize TON logo
        ton_logo.thumbnail((70, 70))
        
        # Colorize TON logo with dominant color
        ton_logo_colored = Image.new('RGBA', ton_logo.size, (0, 0, 0, 0))
        for y in range(ton_logo.height):
            for x in range(ton_logo.width):
                r, g, b, a = ton_logo.getpixel((x, y))
                if a > 0:  # If not fully transparent
                    # Replace black with the dominant color, keeping alpha
                    ton_logo_colored.putpixel((x, y), dominant_color + (a,))
        
        # Load and colorize Star logo
        star_logo = Image.open(STAR_LOGO_PATH)
        if star_logo.mode != 'RGBA':
            star_logo = star_logo.convert('RGBA')
        
        # Resize Star logo
        star_logo.thumbnail((70, 70))
        
        # Colorize Star logo with dominant color
        star_logo_colored = Image.new('RGBA', star_logo.size, (0, 0, 0, 0))
        for y in range(star_logo.height):
            for x in range(star_logo.width):
                r, g, b, a = star_logo.getpixel((x, y))
                if a > 0:  # If not fully transparent
                    # Replace black with the dominant color, keeping alpha
                    star_logo_colored.putpixel((x, y), dominant_color + (a,))
        
        # Position and draw TON logo and price - use exact positions from gift card
        ton_y = y_center + 480
        
        # Calculate logo center point
        ton_logo_center_y = (ton_y - 15) + (ton_logo.height // 2)
        
        # Move text up to properly center with logo
        text_center_offset = ton_price_font.size // 2
        ton_text_y = ton_logo_center_y - text_center_offset
        
        # Paste TON logo
        template.paste(ton_logo_colored, (dollar_x, ton_y - 15), ton_logo_colored)
        
        # Get the width of the TON value text for centering
        ton_text_width = draw.textlength(f"{price:.1f}".replace(".", ",").replace(",0", ""), font=ton_price_font)
        
        # Position TON value
        ton_text_x = dollar_x + 80
        draw.text((ton_text_x, ton_text_y), f"{price:.1f}".replace(".", ",").replace(",0", ""), fill=price_color, font=ton_price_font)
        
        # Draw dot separator
        dot_y = ton_logo_center_y
        dot_x = int(ton_text_x + ton_text_width + 30)
        draw.ellipse((dot_x - 7, dot_y - 7, dot_x + 8, dot_y + 8), fill=(100, 100, 100))
        
        # Position and draw Star logo and price
        star_x = int(dot_x + 20)
        template.paste(star_logo_colored, (star_x, ton_y - 15), star_logo_colored)
        
        # Draw Star price
        star_text_x = star_x + 80
        draw.text((star_text_x, ton_text_y), f"{stars_price:,}".replace(",", " "), fill=price_color, font=ton_price_font)
        
        # Save the card
        output_filename = f"{collection_norm}_{sticker_norm}_price_card.png"
        output_path = os.path.join(output_dir, output_filename)
        template.save(output_path)
        
        logger.info(f"Generated price card: {output_path}")
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
    # Set global variable
    global PRICE_DATA_FILE
    
    parser = argparse.ArgumentParser(description="Generate sticker price cards")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory for generated cards")
    parser.add_argument("--collection", help="Generate card for specific collection")
    parser.add_argument("--sticker", help="Generate card for specific sticker")
    parser.add_argument("--price-file", default=PRICE_DATA_FILE, help="Price data JSON file")
    
    args = parser.parse_args()
    
    # Set price data file
    PRICE_DATA_FILE = args.price_file
    
    # Load price data
    price_data = load_price_data()
    if not price_data:
        logger.error(f"Failed to load price data from {PRICE_DATA_FILE}")
        sys.exit(1)
    
    # Generate cards
    if args.collection and args.sticker:
        # Generate single card
        price = get_sticker_price(price_data, args.collection, args.sticker)
        if price:
            generate_price_card(args.collection, args.sticker, price, args.output_dir)
        else:
            logger.error(f"No price found for {args.collection} - {args.sticker}")
    else:
        # Generate all cards
        generate_all_price_cards(price_data, args.output_dir)

if __name__ == "__main__":
    main() 