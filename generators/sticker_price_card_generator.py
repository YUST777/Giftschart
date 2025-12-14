#!/usr/bin/env python3
"""
Sticker Price Card Generator

This script generates sticker price cards using a modern design with the sticker's
dominant color as background and a white rounded box for content.
It uses the MRKT API to get real-time price data for stickers.
"""

import os
import sys

# Add project root to path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import json
import logging
import argparse
import datetime
import time
import io
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
import numpy as np
import colorsys
import services.stickers_tools_api as sticker_api

# Try to import cairosvg for SVG support (optional)
try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except ImportError:
    CAIROSVG_AVAILABLE = False

# Try to import svglib for fallback SVG support
try:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM
    SVGLIB_AVAILABLE = True
except ImportError:
    SVGLIB_AVAILABLE = False

# Hardcoded data import removed
hsd = None

# Import initial sticker data
# No longer using hardcoded initial data - using API data instead
sid = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sticker_price_card_generator')

# Get script directory for cross-platform compatibility
_project_root = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(_project_root) != 'giftschart':
    _project_root = os.path.dirname(_project_root)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Import centralized paths
from config.paths import (
    PROJECT_ROOT, ASSETS_DIR, STICKER_COLLECTIONS_DIR, 
    STICKER_PRICE_RESULTS_FILE, MAIN_FONT_PATH, 
    STICKER_PRICE_CARDS_DIR, CARD_TEMPLATES_DIR
)

# Constants
TEMPLATES_DIR = CARD_TEMPLATES_DIR
OUTPUT_DIR = STICKER_PRICE_CARDS_DIR
PRICE_DATA_FILE = STICKER_PRICE_RESULTS_FILE
TON_LOGO_PATH = os.path.join(ASSETS_DIR, "TON2.webp")
TRIANGLE_LOGO_PATH = os.path.join(ASSETS_DIR, "triangle.webp")
STAR_LOGO_PATH = os.path.join(ASSETS_DIR, "star.webp")
FONT_PATH = MAIN_FONT_PATH
CACHE_MAX_AGE = 1800  # 30 minutes in seconds

# Global variables for tracking cache vs live API usage
cached_usage = 0
live_api_usage = 0

# Card dimensions
CARD_WIDTH = 1600
CARD_HEIGHT = 1000
WHITE_BOX_WIDTH = 1400
WHITE_BOX_HEIGHT = 800
WHITE_BOX_RADIUS = 40

# Import TON price utility
try:
    from ton_price_utils import get_ton_price_usd
except ImportError:
    # Fallback if module not available
    def get_ton_price_usd():
        return 2.10  # Fallback value

# Windows-safe print function
def safe_print(text):
    """Print text safely on Windows by handling Unicode issues"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Replace problematic characters with safe alternatives
        safe_text = text.replace('⏰', '[TIME]').replace('✅', '[OK]').replace('❌', '[ERROR]').replace('📊', '[STATS]').replace('🎯', '[TARGET]').replace('📅', '[TIME]').replace('📂', '[FILE]').replace('⚠️', '[WARN]').replace('⚡', '[FAST]').replace('⏱️', '[TIME]')
        try:
            print(safe_text)
        except UnicodeEncodeError:
            # If still fails, use a more aggressive replacement
            safe_text = safe_text.encode('ascii', 'ignore').decode('ascii')
            print(safe_text)

def find_image_file(base_path):
    """Find image file, trying .webp first, then .png/.jpg as fallback"""
    webp_path = base_path.rsplit('.', 1)[0] + '.webp' if '.' in base_path else base_path + '.webp'
    png_path = base_path.rsplit('.', 1)[0] + '.webp' if '.' in base_path else base_path + '.webp'
    jpg_path = base_path.rsplit('.', 1)[0] + '.jpg' if '.' in base_path else base_path + '.jpg'
    
    if os.path.exists(webp_path):
        return webp_path
    elif os.path.exists(png_path):
        return png_path
    elif os.path.exists(jpg_path):
        return jpg_path
    else:
        return base_path  # Return original if none exists

def normalize_name(name):
    name = name.strip().lower()
    name = re.sub(r'[^a-z0-9]', '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip('_')

def prettify_name(name):
    # Replace underscores with spaces and capitalize each word
    return ' '.join(word.capitalize() for word in name.replace('_', ' ').split())

def load_price_data():
    """Load price data from the JSON file"""
    try:
        # Check if the file exists
        if not os.path.exists(PRICE_DATA_FILE):
            logger.warning(f"Price data file {PRICE_DATA_FILE} not found")
            return None
        
        # Load the data
        with open(PRICE_DATA_FILE, 'r') as f:
            data = json.load(f)
        
        # Check if the data is older than CACHE_MAX_AGE
        current_time = time.time()
        cached_timestamp = data.get('timestamp', 0)
        
        # Convert string timestamp to float if needed
        if isinstance(cached_timestamp, str):
            try:
                # Try to parse ISO format timestamp
                from datetime import datetime
                dt = datetime.fromisoformat(cached_timestamp.replace('Z', '+00:00'))
                cached_timestamp = dt.timestamp()
            except:
                # If parsing fails, set to 0 to force refresh
                cached_timestamp = 0
        
        if current_time - cached_timestamp > CACHE_MAX_AGE:
            logger.info(f"Cached price data is older than {CACHE_MAX_AGE} seconds, refreshing...")
            safe_print(f"[TIME] CACHE EXPIRED: Price data is older than {CACHE_MAX_AGE/60:.1f} minutes, refreshing...")
            
            # Import here to avoid circular imports
            try:
                import update_sticker_prices
                # Update the price data
                update_sticker_prices.update_sticker_prices()
                
                # Reload the data
                with open(PRICE_DATA_FILE, 'r') as f:
                    data = json.load(f)
                
                logger.info("Price data refreshed successfully")
                safe_print("[OK] REFRESHED: Price data updated successfully")
            except ImportError:
                logger.warning("update_sticker_prices module not available, using cached data")
        
        return data
    except Exception as e:
        logger.error(f"Error loading price data: {e}")
        return None

def load_icon(filename, size=(60, 60), color=None):
    """Load icon from assets (WebP/PNG) and optionally colorize it"""
    try:
        base_name = os.path.splitext(filename)[0]
        
        # Try WebP first, then PNG
        for ext in ['.webp', '.png', '.svg']:
            path = os.path.join(ASSETS_DIR, f"{base_name}{ext}")
            if not os.path.exists(path):
                continue
                
            if ext == '.svg':
                if CAIROSVG_AVAILABLE:
                    # Use cairosvg
                    with open(path, 'r') as f:
                        svg_content = f.read()
                    if color:
                         color_hex = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2]).upper()
                         svg_content = re.sub(r'fill="#1[Cc]274[Cc]"', f'fill="{color_hex}"', svg_content, flags=re.IGNORECASE)
                         svg_content = svg_content.replace('#1C274C', color_hex)
                    png_data = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'), output_width=size[0], output_height=size[1])
                    return Image.open(io.BytesIO(png_data)).convert('RGBA')
                
                elif SVGLIB_AVAILABLE:
                    # Use svglib fallback
                    try:
                        drawing = svg2rlg(path)
                        # SVGLIB doesn't support easy dynamic recoloring of loaded drawing easily without traversal
                        # But we can colorize the result PNG
                        
                        # Render to PNG
                        png_data = renderPM.drawToString(drawing, fmt='PNG')
                        img = Image.open(io.BytesIO(png_data)).convert('RGBA')
                        img = img.resize(size, Image.Resampling.LANCZOS)
                        
                        # Re-colorize if needed because we didn't modify SVG
                        if color:
                             colored = Image.new('RGBA', img.size, (*color, 255))
                             colored.putalpha(img.getchannel('A'))
                             return colored
                        return img
                    except Exception as e:
                        logger.warning(f"SVGLIB conversion failed for {path}: {e}")
                        continue
                
                else:
                    continue

            # Load Raster Image
            img = Image.open(path).convert("RGBA")
            img = img.resize(size, Image.Resampling.LANCZOS)
            
            if color:
                # Colorize using alpha mask
                # Create a solid color image
                colored = Image.new('RGBA', img.size, (*color, 255))
                # Apply the alpha channel from the original image
                colored.putalpha(img.getchannel('A'))
                return colored
            
            return img
            
        return None
    except Exception as e:
        logger.warning(f"Error loading icon {filename}: {e}")
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

def find_sticker_image(collection_norm, sticker_norm):
    """Find the sticker image in the sticker collections directory"""
    try:
        collection_dir = os.path.join(STICKER_COLLECTIONS_DIR, collection_norm)
        if os.path.exists(collection_dir):
            sticker_dir = os.path.join(collection_dir, sticker_norm)
            if os.path.exists(sticker_dir):
                for file in os.listdir(sticker_dir):
                    # Try WebP first
                    if re.match(r'^\d+(_|\.)?webp$', file):
                        return os.path.join(sticker_dir, file)
                    if file.endswith('.webp') or file.endswith('_webp'):
                        return os.path.join(sticker_dir, file)
                    # Then PNG/JPG
                    if re.match(r'^\d+(_|\.)?png$', file) or re.match(r'^\d+(_|\.)?jpg$', file):
                        return os.path.join(sticker_dir, file)
                    if file.endswith('.webp') or file.endswith('.jpg') or file.endswith('_png') or file.endswith('_jpg'):
                        return os.path.join(sticker_dir, file)
    except Exception as e:
        logger.error(f"Error finding sticker image: {e}")
    return None

def find_template_case_insensitive(collection_norm, sticker_norm):
    """Find template file with case-insensitive matching"""
    # Try WebP first, then PNG
    base_name = f"{collection_norm}_{sticker_norm}_template"
    template_path = find_image_file(os.path.join(TEMPLATES_DIR, base_name))
    if os.path.exists(template_path):
        return template_path
    
    # Try with lowercase sticker name
    base_name = f"{collection_norm}_{sticker_norm.lower()}_template"
    template_path = find_image_file(os.path.join(TEMPLATES_DIR, base_name))
    if os.path.exists(template_path):
        return template_path
    
    # Try with lowercase collection and sticker name
    base_name = f"{collection_norm.lower()}_{sticker_norm.lower()}_template"
    template_path = find_image_file(os.path.join(TEMPLATES_DIR, base_name))
    if os.path.exists(template_path):
        return template_path
    
    # Try to find any matching file by listing directory and comparing case-insensitive
    try:
        for filename in os.listdir(TEMPLATES_DIR):
            expected_name = f"{collection_norm}_{sticker_norm}_template.webp".lower()
            if filename.lower() == expected_name:
                return os.path.join(TEMPLATES_DIR, filename)
    except Exception as e:
        logger.error(f"Error searching for template: {e}")
    
    return None

def create_rounded_rectangle(draw, xy, radius, fill):
    """Draw a rounded rectangle"""
    x1, y1, x2, y2 = xy
    
    # Draw the main rectangle
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    
    # Draw the corners
    draw.pieslice([x1, y1, x1 + 2 * radius, y1 + 2 * radius], 180, 270, fill=fill)
    draw.pieslice([x2 - 2 * radius, y1, x2, y1 + 2 * radius], 270, 360, fill=fill)
    draw.pieslice([x1, y2 - 2 * radius, x1 + 2 * radius, y2], 90, 180, fill=fill)
    draw.pieslice([x2 - 2 * radius, y2 - 2 * radius, x2, y2], 0, 90, fill=fill)

def create_gradient_background(width, height, color):
    """Create a radial gradient background based on the dominant color (same as gift cards)"""
    # Create a new image with RGBA mode
    background = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    # Extract RGB components from the dominant color
    r, g, b = color
    
    # Create a darker shade for the edges
    darker_r = max(0, int(r * 0.65))
    darker_g = max(0, int(g * 0.65))
    darker_b = max(0, int(b * 0.65))
    darker_color = (darker_r, darker_g, darker_b, 255)
    
    # Create a lighter shade for the center
    lighter_r = min(255, int(r * 1.15))
    lighter_g = min(255, int(g * 1.15))
    lighter_b = min(255, int(b * 1.15))
    lighter_color = (lighter_r, lighter_g, lighter_b, 255)
    
    # Create a slightly different hue for added depth
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    h = (h + 0.05) % 1.0  # Shift hue slightly
    s = min(1.0, s * 1.2)  # Increase saturation
    accent_r, accent_g, accent_b = colorsys.hsv_to_rgb(h, s, v)
    accent_color = (int(accent_r*255), int(accent_g*255), int(accent_b*255), 255)
    
    # Create a radial gradient using the same method as gift cards
    # First create a small gradient image and then resize it
    small_size = (200, 200)  # Increased for smoother gradient
    small_gradient = Image.new('RGBA', small_size, (0, 0, 0, 0))
    small_draw = ImageDraw.Draw(small_gradient)
    
    # Draw concentric circles with decreasing radius
    center = (small_size[0] // 2, small_size[1] // 2)
    max_radius = int(((small_size[0] // 2) ** 2 + (small_size[1] // 2) ** 2) ** 0.5)
    
    # Draw from outside in with more gradual transitions
    num_steps = 40  # More steps for smoother gradient
    for i in range(num_steps):
        # Calculate radius for this step
        radius = max_radius * (1 - (i / num_steps))
        
        # Calculate interpolation factor (0 at edge, 1 at center)
        factor = i / num_steps
        
        # Create multi-point gradient with darker outer edges and lighter center
        if factor < 0.25:  # Outer 25% transitions from darker to base
            t = factor / 0.25
            r_val = int(darker_color[0] * (1-t) + color[0] * t)
            g_val = int(darker_color[1] * (1-t) + color[1] * t)
            b_val = int(darker_color[2] * (1-t) + color[2] * t)
        elif factor < 0.5:  # Next 25% transitions from base to accent
            t = (factor - 0.25) / 0.25
            r_val = int(color[0] * (1-t) + accent_color[0] * t)
            g_val = int(color[1] * (1-t) + accent_color[1] * t)
            b_val = int(color[2] * (1-t) + accent_color[2] * t)
        else:  # Inner 50% transitions from accent to lighter
            t = (factor - 0.5) / 0.5
            r_val = int(accent_color[0] * (1-t) + lighter_color[0] * t)
            g_val = int(accent_color[1] * (1-t) + lighter_color[1] * t)
            b_val = int(accent_color[2] * (1-t) + lighter_color[2] * t)
        
        current_color = (r_val, g_val, b_val, 255)
        
        # Draw a filled circle
        bbox = (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius)
        small_draw.ellipse(bbox, fill=current_color)
    
    # Resize the small gradient to the full size
    gradient_bg = small_gradient.resize((width, height), Image.BICUBIC)
    
    return gradient_bg

def generate_price_card(collection, sticker, price, output_dir):
    """Generate a price card for a sticker using the new modern design"""
    try:
        # Normalize names for file operations
        collection_norm = normalize_name(collection)
        sticker_norm = normalize_name(sticker)
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get price info from stickers.tools API
        price_info = sticker_api.get_sticker_price(collection, sticker, force_refresh=False)
        if not price_info:
            logger.warning(f"No price info for {collection} - {sticker}")
            return None
        price_ton = price_info['floor_price_ton']
        price_usd = price_info['floor_price_usd']
        supply = price_info['supply']
        initial_supply = price_info.get('initial_supply', 0)
        init_price_usd = price_info.get('init_price_usd', 0)
        
        # Find sticker image
        sticker_image_path = find_sticker_image(collection_norm, sticker_norm)
        dominant_color = None
        
        if not sticker_image_path:
            logger.warning(f"Sticker image not found for {collection} - {sticker}")
            # Try to find a template to use for dominant color
            template_path = find_template_case_insensitive(collection_norm, sticker_norm)
            if template_path:
                dominant_color = get_dominant_color(template_path)
                logger.info(f"Using template for dominant color: {template_path}")
            else:
                # Use a default color scheme based on collection
                default_colors = {
                    'Dogs_OG': (255, 165, 0),      # Orange for Dogs OG
                    'Blum': (0, 191, 255),         # Sky blue for Blum
                    'Not_Pixel': (255, 20, 147),   # Deep pink for Not Pixel
                    'Pudgy_Penguins': (70, 130, 180), # Steel blue for Pudgy
                    'Bored_Stickers': (138, 43, 226), # Blue violet for Bored
                    'Doodles': (255, 105, 180),    # Hot pink for Doodles
                }
                dominant_color = default_colors.get(collection_norm, (148, 68, 143))  # Default purple
                logger.info(f"Using default color scheme for {collection}: {dominant_color}")
        else:
            dominant_color = get_dominant_color(sticker_image_path)
            logger.info(f"Using sticker image: {sticker_image_path}")
        
        # Create a gradient background instead of solid color
        card = create_gradient_background(CARD_WIDTH, CARD_HEIGHT, dominant_color)
        draw = ImageDraw.Draw(card)
        
        # Calculate center position for white box
        white_box_x = (CARD_WIDTH - WHITE_BOX_WIDTH) // 2
        white_box_y = (CARD_HEIGHT - WHITE_BOX_HEIGHT) // 2
        
        # Draw white rounded rectangle
        create_rounded_rectangle(
            draw, 
            (white_box_x, white_box_y, white_box_x + WHITE_BOX_WIDTH, white_box_y + WHITE_BOX_HEIGHT),
            WHITE_BOX_RADIUS,
            (255, 255, 255, 255)  # White color
        )
        
        # Load fonts
        try:
            title_font = ImageFont.truetype(FONT_PATH, 80)  # For collection name
            subtitle_font = ImageFont.truetype(FONT_PATH, 60)  # For sticker name
            price_font = ImageFont.truetype(FONT_PATH, 180)  # For USD price
            ton_price_font = ImageFont.truetype(FONT_PATH, 50)  # For TON price
            date_font = ImageFont.truetype(FONT_PATH, 30)  # For date at the bottom
            watermark_font = ImageFont.truetype(FONT_PATH, 40)  # For bot watermark
        except Exception as e:
            logger.error(f"Error loading font: {e}")
            # Fallback to default font
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            price_font = ImageFont.load_default()
            ton_price_font = ImageFont.load_default()
            date_font = ImageFont.load_default()
            watermark_font = ImageFont.load_default()
        
        # Draw bot watermark at the top center
        watermark_lines = ["@GiftsChartbot"]
        watermark_font = ImageFont.truetype(FONT_PATH, 32) if os.path.exists(FONT_PATH) else ImageFont.load_default()
        line_height = watermark_font.getbbox("A")[3] + 5
        watermark_y = 30  # Start position
        
        # Draw each line centered
        for i, line in enumerate(watermark_lines):
            line_bbox = draw.textbbox((0, 0), line, font=watermark_font)
            line_width = line_bbox[2] - line_bbox[0]
            watermark_x = (CARD_WIDTH - line_width) // 2
            line_y = watermark_y + (i * line_height)
            draw.text((watermark_x, line_y), line, fill=(255, 255, 255, 200), font=watermark_font)
        
        # Draw collection name
        display_collection = prettify_name(collection)
        collection_x = white_box_x + 60
        collection_y = white_box_y + 60
        draw.text((collection_x, collection_y), display_collection, fill=(20, 20, 20), font=title_font)
        
        # Draw sticker name
        display_sticker = prettify_name(sticker)
        sticker_y = collection_y + title_font.getbbox("A")[3] + 10  # Add some spacing
        draw.text((collection_x, sticker_y), display_sticker, fill=(80, 80, 80), font=subtitle_font)
        
        # Calculate USD price using real TON price
        ton_price_usd = get_ton_price_usd()
        price_usd = price * ton_price_usd
        
        # Draw dollar sign in lighter color (using dominant color with transparency)
        dollar_color = (*dominant_color[:3], 150)  # Use dominant color with transparency
        dollar_x = collection_x + 20
        dollar_y = sticker_y + subtitle_font.getbbox("A")[3] + 50  # Add spacing after sticker name
        draw.text((dollar_x, dollar_y), "$", fill=dollar_color, font=price_font)
        
        # Draw USD price
        price_text = f"{price_usd:,.0f}".replace(",", " ")
        price_x = dollar_x + price_font.getbbox("$")[2] + 10  # Add spacing after dollar sign
        draw.text((price_x, dollar_y), price_text, fill=(20, 20, 20), font=price_font)
        
        # Draw horizontal line - half width on x-axis
        line_y = dollar_y + price_font.getbbox("$")[3] + 15
        line_width = (white_box_x + WHITE_BOX_WIDTH - 60 - collection_x) // 2  # Half the width
        draw.line([(collection_x, line_y), (collection_x + line_width, line_y)], fill=(200, 200, 200), width=3)  # Increased width from 1 to 3
        
        # Draw TON price with TON logo beside the $ price instead of below it
        ton_text = f"{price_ton:.1f}".replace(".", ",").replace(",0", "")
        
        # Calculate position for TON price (beside the USD price)
        usd_price_width = draw.textlength(price_text, font=price_font)
        ton_x = price_x + usd_price_width + 30  # Position after USD price with some spacing
        ton_y = dollar_y + price_font.getbbox("$")[3] - ton_price_font.getbbox("A")[3] - 10  # Align bottom with USD price
        
        # Add TON logo before TON price
        try:
            ton_logo = Image.open(TON_LOGO_PATH).convert("RGBA")
            ton_logo = ton_logo.resize((60, 60))  # Same size as supply and star icons
            
            # Extract the alpha channel to use as a mask
            r, g, b, alpha = ton_logo.split()
            
            # Create a new image with the background color
            colored_ton_logo = Image.new('RGBA', ton_logo.size, (*dominant_color, 255))
            
            # Apply the alpha mask from the original image
            colored_ton_logo.putalpha(alpha)
            
            # Calculate vertical position to center the icon with the text
            text_height = ton_price_font.getbbox("0")[3]
            icon_y_offset = (80 - text_height) // 2  # Center the 60px icon with the text
            
            card.paste(colored_ton_logo, (int(ton_x), int(ton_y - icon_y_offset)), colored_ton_logo)
            ton_x += 70  # Space after TON logo
        except Exception as e:
            logger.warning(f"TON logo not found: {e}")
        
        # Draw TON price
        draw.text((ton_x, ton_y), ton_text, fill=(20, 20, 20), font=ton_price_font)
        
        # Get supply and sale price information
        # supply = None # This line is no longer needed as supply is now from price_info

        # Draw supply and initial price on the same line
        if supply:
            info_y = line_y + 30  # Position below the line
            current_x = collection_x
            
            # Calculate proper vertical alignment for icons
            # Get the actual text height for proper centering
            text_bbox = ton_price_font.getbbox("0")
            text_height = text_bbox[3] - text_bbox[1]
            text_top_offset = abs(text_bbox[1])  # Distance from baseline to top
            
            # Calculate icon Y position to center with text baseline
            icon_size = 60
            icon_y_offset = (text_height - icon_size) // 2 + text_top_offset
            
            # Add supply icon (WebP/SVG)
            try:
                supply_icon = load_icon("supply.svg", size=(icon_size, icon_size), color=dominant_color)
                if supply_icon:
                    card.paste(supply_icon, (int(current_x), int(info_y + icon_y_offset)), supply_icon)
                    current_x += icon_size + 10
            except Exception as e:
                logger.warning(f"Supply icon error: {e}")
            
            # Display only current supply (no initial supply)
            supply_text = f"{supply:,}".replace(",", " ")
            
            draw.text((current_x, info_y), supply_text, fill=(81, 81, 81), font=ton_price_font)
            current_x += draw.textlength(supply_text, font=ton_price_font) + 10
            
            # Add initial USD price on the same line if available
            if init_price_usd and init_price_usd > 0:
                # Add separator between supply and initial price
                separator_text = "|"
                draw.text((current_x, info_y), separator_text, fill=(150, 150, 150), font=ton_price_font)
                current_x += draw.textlength(separator_text, font=ton_price_font) + 10
                
                # Add dollar sign as text (no icon)
                dollar_text = "$"
                draw.text((current_x, info_y), dollar_text, fill=(81, 81, 81), font=ton_price_font)
                current_x += draw.textlength(dollar_text, font=ton_price_font) + 5
                
                # Display initial USD price
                initial_price_text = f"{init_price_usd:.0f}".replace(",", " ")
                draw.text((current_x, info_y), initial_price_text, fill=(81, 81, 81), font=ton_price_font)
                current_x += draw.textlength(initial_price_text, font=ton_price_font) + 10
            
            
        
        # Add sticker image on the right side (with fallback for missing images)
        if sticker_image_path:
            try:
                sticker_img = Image.open(sticker_image_path).convert("RGBA")
                
                # Calculate size for the sticker image (reduced by 30% from previous size)
                max_width = 560  # Reduced from 800 by 30%
                max_height = 490  # Reduced from 700 by 30%
                width, height = sticker_img.size
                
                # Calculate new dimensions while maintaining aspect ratio
                if width > height:
                    ratio = min(max_width / width, max_height / height)
                else:
                    ratio = min(max_width / width, max_height / height) * 1.2  # Make it a bit larger if portrait
                
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                sticker_img = sticker_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Calculate position (right side of white box, vertically centered)
                sticker_x = white_box_x + WHITE_BOX_WIDTH - sticker_img.width - 20  # Reduced from 50 to 20 to move more to the right
                sticker_y = white_box_y + (WHITE_BOX_HEIGHT - sticker_img.height) // 2
                
                # Paste sticker image
                card.paste(sticker_img, (sticker_x, sticker_y), sticker_img)
                logger.info(f"Added sticker image: {sticker_image_path}")
            except Exception as e:
                logger.error(f"Error adding sticker image: {e}")
        else:
            # Create placeholder for missing sticker image
            logger.info(f"Creating placeholder for missing sticker image: {collection} - {sticker}")
            placeholder_size = 300
            placeholder_x = white_box_x + WHITE_BOX_WIDTH - placeholder_size - 50
            placeholder_y = white_box_y + (WHITE_BOX_HEIGHT - placeholder_size) // 2
            
            # Draw a rounded rectangle placeholder
            placeholder_color = (*dominant_color, 100)  # Semi-transparent dominant color
            create_rounded_rectangle(
                draw,
                (placeholder_x, placeholder_y, placeholder_x + placeholder_size, placeholder_y + placeholder_size),
                30,  # Rounded corners
                placeholder_color
            )
            
            # Add placeholder text
            try:
                placeholder_font = ImageFont.truetype(FONT_PATH, 40)
            except:
                placeholder_font = ton_price_font
            
            placeholder_text = "No Image\nAvailable"
            text_bbox = draw.multiline_textbbox((0, 0), placeholder_text, font=placeholder_font, align='center')
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = placeholder_x + (placeholder_size - text_width) // 2
            text_y = placeholder_y + (placeholder_size - text_height) // 2
            
            draw.multiline_text((text_x, text_y), placeholder_text, fill=(255, 255, 255, 180), font=placeholder_font, align='center')
        
        # Add generation date at the bottom middle of the card
        current_date = datetime.datetime.now().strftime("%d %b %Y • %H:%M UTC")
        date_text = current_date
        date_text_width = draw.textlength(date_text, font=date_font)
        date_x = CARD_WIDTH // 2 - date_text_width // 2
        date_y = white_box_y + WHITE_BOX_HEIGHT - 50  # Position at bottom of white card area
        draw.text((date_x, date_y), date_text, fill=(100, 100, 100), font=date_font)
        
        # Save the card as WebP
        output_filename = f"{collection_norm}_{sticker_norm}_price_card.webp"
        output_path = os.path.join(output_dir, output_filename)
        card.save(output_path, 'WEBP', quality=85, method=6)
        
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
    
    # Reset counters
    global cached_usage, live_api_usage
    cached_usage = 0
    live_api_usage = 0
    
    # Get stickers
    stickers = price_data['stickers_with_prices']
    total_stickers = len(stickers)
    
    logger.info(f"Generating {total_stickers} price cards...")
    
    # Generate cards for each sticker with price
    for i, item in enumerate(stickers):
        collection = item['collection']
        sticker = item['sticker']
        price = item['price']
        
        logger.info(f"Generating price card for {collection} - {sticker}: {price} TON")
        
        result = generate_price_card(collection, sticker, price, output_dir)
        
        if not result:
            safe_print(f"[WARN] WARNING: Could not get live price data for {collection} - {sticker}")
    
    logger.info(f"Price card generation complete: {cached_usage} from cache, {live_api_usage} from live API")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate sticker price cards")
    parser.add_argument("collection", help="Collection name")
    parser.add_argument("sticker", help="Sticker name")
    parser.add_argument("price", type=float, help="Price in TON")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory")
    
    args = parser.parse_args()
    
    # Generate the price card
    result = generate_price_card(args.collection, args.sticker, args.price, args.output_dir)
    
    if result:
        print(f"Price card generated: {result}")
    else:
        print("Failed to generate price card")

if __name__ == "__main__":
    main() 