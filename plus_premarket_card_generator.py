#!/usr/bin/env python3
"""
Plus Premarket Gift Card Generator
Generates price cards for plus premarket gifts using sticker card design
(No chart data, shows supply and first sale price in stars)
"""

import os
import sys
import logging
import datetime
import io
import re
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import colorsys
from plus_premarket_gifts import (
    PLUS_PREMARKET_GIFTS, get_gift_supply, get_first_sale_price_stars, 
    STAR_TO_USD, get_gift_id, calculate_days_since_release
)

# Try to import premarket gifts functions (for regular premarket gifts)
try:
    from premarket_gifts import (
        is_premarket_gift, get_premarket_supply, get_premarket_first_sale_price_stars,
        calculate_days_since_release as calculate_premarket_days_since_release
    )
    PREMARKET_GIFTS_AVAILABLE = True
except ImportError:
    PREMARKET_GIFTS_AVAILABLE = False

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('plus_premarket_card_generator')

# Get script directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Constants
OUTPUT_DIR = os.path.join(script_dir, "new_gift_cards")
ASSETS_DIR = os.path.join(script_dir, "assets")
DOWNLOADED_IMAGES_DIR = os.path.join(script_dir, "downloaded_images")
TON_LOGO_PATH = os.path.join(ASSETS_DIR, "TON2.webp")
STAR_LOGO_PATH = os.path.join(ASSETS_DIR, "star.webp")
TIME_ICON_PATH = os.path.join(ASSETS_DIR, "time.svg")
FONT_PATH = os.path.join(script_dir, "assets/fonts/Typekiln - EloquiaDisplay-ExtraBold.otf")

# Import TON price utility (not used directly as price_usd comes from API, but available if needed)
try:
    from ton_price_utils import get_ton_price_usd
except ImportError:
    def get_ton_price_usd():
        return 2.10  # Fallback value

# Card dimensions (same as sticker cards)
CARD_WIDTH = 1600
CARD_HEIGHT = 1000
WHITE_BOX_WIDTH = 1400
WHITE_BOX_HEIGHT = 800
WHITE_BOX_RADIUS = 40

def get_dominant_color(image_path):
    """Get the dominant color from an image"""
    try:
        img = Image.open(image_path)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        img.thumbnail((100, 100))
        pixels = list(img.getdata())
        pixels = [p for p in pixels if p[3] > 128]
        
        if not pixels:
            return (128, 128, 128)
        
        r_sum = sum(p[0] for p in pixels)
        g_sum = sum(p[1] for p in pixels)
        b_sum = sum(p[2] for p in pixels)
        count = len(pixels)
        return (r_sum // count, g_sum // count, b_sum // count)
    except Exception as e:
        logger.error(f"Error getting dominant color: {e}")
        return (128, 128, 128)

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
                colored = Image.new('RGBA', img.size, (*color, 255))
                colored.putalpha(img.getchannel('A'))
                return colored
            
            return img
            
        return None
    except Exception as e:
        logger.warning(f"Error loading icon {filename}: {e}")
        return None

def create_rounded_rectangle(draw, xy, radius, fill):
    """Draw a rounded rectangle"""
    x1, y1, x2, y2 = xy
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.pieslice([x1, y1, x1 + 2 * radius, y1 + 2 * radius], 180, 270, fill=fill)
    draw.pieslice([x2 - 2 * radius, y1, x2, y1 + 2 * radius], 270, 360, fill=fill)
    draw.pieslice([x1, y2 - 2 * radius, x1 + 2 * radius, y2], 90, 180, fill=fill)
    draw.pieslice([x2 - 2 * radius, y2 - 2 * radius, x2, y2], 0, 90, fill=fill)

def create_gradient_background(width, height, color):
    """Create a radial gradient background based on the dominant color"""
    background = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    r, g, b = color
    
    darker_r = max(0, int(r * 0.65))
    darker_g = max(0, int(g * 0.65))
    darker_b = max(0, int(b * 0.65))
    darker_color = (darker_r, darker_g, darker_b, 255)
    
    lighter_r = min(255, int(r * 1.15))
    lighter_g = min(255, int(g * 1.15))
    lighter_b = min(255, int(b * 1.15))
    lighter_color = (lighter_r, lighter_g, lighter_b, 255)
    
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    h = (h + 0.05) % 1.0
    s = min(1.0, s * 1.2)
    accent_r, accent_g, accent_b = colorsys.hsv_to_rgb(h, s, v)
    accent_color = (int(accent_r*255), int(accent_g*255), int(accent_b*255), 255)
    
    small_size = (200, 200)
    small_gradient = Image.new('RGBA', small_size, (0, 0, 0, 0))
    small_draw = ImageDraw.Draw(small_gradient)
    
    center = (small_size[0] // 2, small_size[1] // 2)
    max_radius = int(((small_size[0] // 2) ** 2 + (small_size[1] // 2) ** 2) ** 0.5)
    
    num_steps = 40
    for i in range(num_steps):
        radius = max_radius * (1 - (i / num_steps))
        factor = i / num_steps
        
        if factor < 0.25:
            t = factor / 0.25
            r_val = int(darker_color[0] * (1-t) + color[0] * t)
            g_val = int(darker_color[1] * (1-t) + color[1] * t)
            b_val = int(darker_color[2] * (1-t) + color[2] * t)
        elif factor < 0.5:
            t = (factor - 0.25) / 0.25
            r_val = int(color[0] * (1-t) + accent_color[0] * t)
            g_val = int(color[1] * (1-t) + accent_color[1] * t)
            b_val = int(color[2] * (1-t) + accent_color[2] * t)
        else:
            t = (factor - 0.5) / 0.5
            r_val = int(accent_color[0] * (1-t) + lighter_color[0] * t)
            g_val = int(accent_color[1] * (1-t) + lighter_color[1] * t)
            b_val = int(accent_color[2] * (1-t) + lighter_color[2] * t)
        
        current_color = (r_val, g_val, b_val, 255)
        bbox = (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius)
        small_draw.ellipse(bbox, fill=current_color)
    
    gradient_bg = small_gradient.resize((width, height), Image.BICUBIC)
    return gradient_bg

def find_gift_image(gift_name):
    """Find the gift image in downloaded_images directory"""
    # Normalize gift name for filename lookup
    if gift_name == "Jack-in-the-Box":
        normalized_name = "Jack_in_the_Box"
    elif gift_name == "Durov's Cap":
        normalized_name = "Durovs_Cap"
    elif gift_name == "Durov's Statuette":
        normalized_name = "Durovs_Statuette"
    else:
        normalized_name = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
    
    # Try different filename patterns
    # Remove quotes for pattern matching
    no_quotes = gift_name.replace("'", "")
    patterns = [
        f"{normalized_name}.webp",
        f"{normalized_name}.webp",  # Fallback
        f"{gift_name.replace(' ', '_')}.webp",
        f"{gift_name.replace(' ', '_')}.webp",  # Fallback
        f"{no_quotes.replace(' ', '').replace('-', '')}.webp",
        f"{no_quotes.replace(' ', '').replace('-', '')}.webp",  # Fallback
    ]
    
    for pattern in patterns:
        image_path = os.path.join(DOWNLOADED_IMAGES_DIR, pattern)
        if os.path.exists(image_path):
            return image_path
    
    return None

def generate_plus_premarket_card(gift_name, gift_data, output_path=None):
    """Generate a price card for a plus premarket gift using sticker card design"""
    try:
        # Determine output directory and filename
        if output_path:
            output_dir = os.path.dirname(output_path)
            if not output_dir:
                output_dir = OUTPUT_DIR
            output_filename = os.path.basename(output_path)
        else:
            output_dir = OUTPUT_DIR
            safe_name = gift_name.replace(" ", "_").replace("-", "_").replace("'", "").replace("/", "_")
            output_filename = f"{safe_name}.webp"
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Get supply and first sale price
        # Check if this is a regular premarket gift (not +premarket)
        if PREMARKET_GIFTS_AVAILABLE and is_premarket_gift(gift_name):
            # Use premarket gifts functions
            supply = get_premarket_supply(gift_name)
            first_sale_price_stars = get_premarket_first_sale_price_stars(gift_name)
            days_since_release_func = calculate_premarket_days_since_release
        else:
            # Use plus premarket gifts functions
            supply = get_gift_supply(gift_name)
            first_sale_price_stars = get_first_sale_price_stars(gift_name)
            days_since_release_func = calculate_days_since_release
        
        # Extract price data from gift_data
        price_ton = gift_data.get('priceTon', 0)
        price_usd = gift_data.get('priceUsd', 0)
        
        # Convert to float if needed
        if isinstance(price_ton, dict):
            price_ton = 0
        if isinstance(price_usd, dict):
            price_usd = 0
        
        price_ton = float(price_ton)
        price_usd = float(price_usd)
        
        # Calculate star price from USD (1 star = $0.016)
        star_price = int(price_usd / STAR_TO_USD)
        
        # Calculate first sale price in USD
        first_sale_price_usd = first_sale_price_stars * STAR_TO_USD if first_sale_price_stars else None
        
        # Find gift image
        gift_image_path = find_gift_image(gift_name)
        dominant_color = None
        
        if gift_image_path:
            dominant_color = get_dominant_color(gift_image_path)
            logger.info(f"Using gift image: {gift_image_path}")
        else:
            logger.warning(f"Gift image not found for {gift_name}, using default color")
            dominant_color = (148, 68, 143)  # Default purple
        
        # Create gradient background
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
            (255, 255, 255, 255)
        )
        
        # Load fonts
        try:
            title_font = ImageFont.truetype(FONT_PATH, 80)  # For gift name
            price_font = ImageFont.truetype(FONT_PATH, 180)  # For USD price
            ton_price_font = ImageFont.truetype(FONT_PATH, 50)  # For TON/Star prices
            date_font = ImageFont.truetype(FONT_PATH, 30)  # For date
            watermark_font = ImageFont.truetype(FONT_PATH, 40)  # For watermark
        except Exception as e:
            logger.error(f"Error loading font: {e}")
            title_font = ImageFont.load_default()
            price_font = ImageFont.load_default()
            ton_price_font = ImageFont.load_default()
            date_font = ImageFont.load_default()
            watermark_font = ImageFont.load_default()
        
        # Draw bot watermark at top center
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
        
        # Draw gift name
        collection_x = white_box_x + 60
        collection_y = white_box_y + 60
        draw.text((collection_x, collection_y), gift_name, fill=(20, 20, 20), font=title_font)
        
        # Draw dollar sign and USD price
        dollar_color = (*dominant_color[:3], 150)
        dollar_x = collection_x + 20
        dollar_y = collection_y + title_font.getbbox("A")[3] + 50
        draw.text((dollar_x, dollar_y), "$", fill=dollar_color, font=price_font)
        
        price_text = f"{price_usd:,.0f}".replace(",", " ")
        price_x = dollar_x + price_font.getbbox("$")[2] + 10
        draw.text((price_x, dollar_y), price_text, fill=(20, 20, 20), font=price_font)
        
        # Draw horizontal line
        line_y = dollar_y + price_font.getbbox("$")[3] + 15
        line_width = (white_box_x + WHITE_BOX_WIDTH - 60 - collection_x) // 2
        draw.line([(collection_x, line_y), (collection_x + line_width, line_y)], fill=(200, 200, 200), width=3)
        
        # Draw TON price with TON logo
        ton_text = f"{price_ton:.1f}".replace(".", ",").replace(",0", "")
        usd_price_width = draw.textlength(price_text, font=price_font)
        ton_x = price_x + usd_price_width + 30
        ton_y = dollar_y + price_font.getbbox("$")[3] - ton_price_font.getbbox("A")[3] - 10
        
        # Add TON logo
        try:
            ton_logo = Image.open(TON_LOGO_PATH).convert("RGBA")
            ton_logo = ton_logo.resize((60, 60))
            r, g, b, alpha = ton_logo.split()
            colored_ton_logo = Image.new('RGBA', ton_logo.size, (*dominant_color, 255))
            colored_ton_logo.putalpha(alpha)
            text_height = ton_price_font.getbbox("0")[3]
            icon_y_offset = (80 - text_height) // 2
            card.paste(colored_ton_logo, (int(ton_x), int(ton_y - icon_y_offset)), colored_ton_logo)
            ton_x += 70
        except Exception as e:
            logger.warning(f"TON logo not found: {e}")
        
        draw.text((ton_x, ton_y), ton_text, fill=(20, 20, 20), font=ton_price_font)
        
        # Draw supply and first sale price
        if supply:
            info_y = line_y + 30
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
            
            # Display supply
            supply_text = f"{supply:,}".replace(",", " ")
            draw.text((current_x, info_y), supply_text, fill=(81, 81, 81), font=ton_price_font)
            current_x += draw.textlength(supply_text, font=ton_price_font) + 10
            
            # Add first sale price in stars if available
            if first_sale_price_stars:
                separator_text = "|"
                draw.text((current_x, info_y), separator_text, fill=(150, 150, 150), font=ton_price_font)
                current_x += draw.textlength(separator_text, font=ton_price_font) + 10
                
                # Add star icon for first sale price (PNG)
                try:
                    if os.path.exists(STAR_LOGO_PATH):
                        first_star_logo = Image.open(STAR_LOGO_PATH).convert("RGBA")
                        first_star_logo = first_star_logo.resize((icon_size, icon_size))
                        r, g, b, alpha = first_star_logo.split()
                        colored_first_star = Image.new('RGBA', first_star_logo.size, (*dominant_color, 255))
                        colored_first_star.putalpha(alpha)
                        card.paste(colored_first_star, (int(current_x), int(info_y + icon_y_offset)), colored_first_star)
                        current_x += icon_size + 10
                except Exception as e:
                    logger.warning(f"Star logo not found for first sale: {e}")
                
                # Display first sale price in stars
                first_sale_text = f"{first_sale_price_stars:,}".replace(",", " ")
                draw.text((current_x, info_y), first_sale_text, fill=(81, 81, 81), font=ton_price_font)
                current_x += draw.textlength(first_sale_text, font=ton_price_font) + 10
                
                # Add days since release with time icon
                days_since_release = days_since_release_func(gift_name)
                if days_since_release is not None and days_since_release >= 0:
                    # Add separator
                    separator_text = "|"
                    draw.text((current_x, info_y), separator_text, fill=(150, 150, 150), font=ton_price_font)
                    current_x += draw.textlength(separator_text, font=ton_price_font) + 10
                    
                    # Choose icon based on gift type: premarket uses cart icon, +premarket uses time icon
                    if PREMARKET_GIFTS_AVAILABLE and is_premarket_gift(gift_name):
                        # Use cart icon for premarket gifts
                        icon_filename = "premarket_cart.svg"
                    else:
                        # Use time icon for +premarket gifts
                        icon_filename = "time.svg"
                    
                    # Add icon (WebP/SVG)
                    try:
                        date_icon = load_icon(icon_filename, size=(icon_size, icon_size), color=dominant_color)
                        if date_icon:
                            card.paste(date_icon, (int(current_x), int(info_y + icon_y_offset)), date_icon)
                            current_x += icon_size + 10
                        else:
                            logger.warning(f"{icon_filename} icon could not be loaded")
                    except Exception as e:
                        logger.warning(f"Date icon error: {e}")
                    
                    # Display days since release (just the number)
                    days_text = f"{days_since_release}"
                    draw.text((current_x, info_y), days_text, fill=(81, 81, 81), font=ton_price_font)
        
        # Add gift image on the right side
        if gift_image_path:
            try:
                gift_img = Image.open(gift_image_path).convert("RGBA")
                max_width = 560
                max_height = 490
                width, height = gift_img.size
                
                if width > height:
                    ratio = min(max_width / width, max_height / height)
                else:
                    ratio = min(max_width / width, max_height / height) * 1.2
                
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                gift_img = gift_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                gift_x = white_box_x + WHITE_BOX_WIDTH - gift_img.width - 20
                gift_y = white_box_y + (WHITE_BOX_HEIGHT - gift_img.height) // 2
                
                card.paste(gift_img, (gift_x, gift_y), gift_img)
                logger.info(f"Added gift image: {gift_image_path}")
            except Exception as e:
                logger.error(f"Error adding gift image: {e}")
        
        # Add generation date at bottom
        current_date = datetime.datetime.now().strftime("%d %b %Y • %H:%M UTC")
        date_text_width = draw.textlength(current_date, font=date_font)
        date_x = CARD_WIDTH // 2 - date_text_width // 2
        date_y = white_box_y + WHITE_BOX_HEIGHT - 50
        draw.text((date_x, date_y), current_date, fill=(100, 100, 100), font=date_font)
        
        # Save the card as WebP
        final_output_path = os.path.join(output_dir, output_filename)
        # Ensure correct extension (fix double-dot bug caused by [:-4] on .webp)
        if final_output_path.lower().endswith('.webp'):
            # It's already correct, do nothing (or ensure casing)
            pass
        else:
            final_output_path += '.webp'
            
        card.save(final_output_path, 'WEBP', quality=85, method=6)
        
        logger.info(f"Generated plus premarket card: {final_output_path}")
        return card
    except Exception as e:
        logger.error(f"Error generating card for {gift_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

