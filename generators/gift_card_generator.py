import os
import sys

# Add project root to path for config imports
_project_root = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(_project_root) != 'giftschart':
    _project_root = os.path.dirname(_project_root)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import random
from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageStat, ImageEnhance, ImageFilter, ImageOps
import colorsys
import numpy as np
import datetime
import requests
import json
from urllib.parse import quote
from difflib import get_close_matches
import math
import logging

# Import our Portal API module (replaces Tonnel API)
import services.portal_api as portal_api
import asyncio

# Import centralized paths
from config.paths import (
    PROJECT_ROOT, DOWNLOADED_IMAGES_DIR, GIFT_CARDS_DIR, ASSETS_DIR, 
    PREGENERATED_BACKGROUNDS_DIR, MAIN_FONT_PATH, GIFT_API_RESULTS_LOG,
    MRKT_API_DIR
)

# Set up detailed logging for API results and debugging
api_logger = logging.getLogger("gift_api_results")
api_logger.setLevel(logging.INFO)
api_log_handler = logging.FileHandler(GIFT_API_RESULTS_LOG)
api_log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == api_log_handler.baseFilename for h in api_logger.handlers):
    api_logger.addHandler(api_log_handler)

# Configure main logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Directory paths - using centralized config
input_dir = DOWNLOADED_IMAGES_DIR
output_dir = GIFT_CARDS_DIR
assets_dir = ASSETS_DIR
backgrounds_dir = PREGENERATED_BACKGROUNDS_DIR
background_path = os.path.join(assets_dir, "Background color this.webp")
white_box_path = os.path.join(assets_dir, "white box.webp")
ton_logo_path = os.path.join(assets_dir, "TON2.webp")
star_logo_path = os.path.join(assets_dir, "star.webp")
font_path = MAIN_FONT_PATH

# Helper function to find image file (tries .webp first, then .png)
def find_image_file(base_path):
    """Find image file, trying .webp first, then .png as fallback"""
    webp_path = base_path.rsplit('.', 1)[0] + '.webp' if '.' in base_path else base_path + '.webp'
    png_path = base_path.rsplit('.', 1)[0] + '.webp' if '.' in base_path else base_path + '.webp'
    
    if os.path.exists(webp_path):
        return webp_path
    elif os.path.exists(png_path):
        return png_path
    else:
        return base_path  # Return original if neither exists

# API endpoints (kept as fallback)
GIFTS_API = "https://giftcharts-api.onrender.com/gifts"
CHART_API = "https://giftcharts-api.onrender.com/weekChart?name="

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)
os.makedirs(backgrounds_dir, exist_ok=True)  # Ensure backgrounds directory exists

# Function to get dominant color from an image
def get_dominant_color(image_path):
    try:
        img = Image.open(image_path)
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create a smaller version of the image to speed up processing
        img.thumbnail((100, 100))
        
        # Get color data
        pixels = np.array(img)
        
        # Remove transparent pixels (alpha < 128)
        pixels = pixels[pixels[:,:,3] > 128]
        
        if len(pixels) == 0:
            return (128, 128, 128)  # Default to gray if all pixels are transparent
        
        # Remove alpha channel for clustering
        pixels = pixels[:,:3]
        
        # Simple average color (mean of all non-transparent pixels)
        avg_color = pixels.mean(axis=0).astype(int)
        
        # Enhance saturation a bit for better visual appeal
        h, s, v = colorsys.rgb_to_hsv(avg_color[0]/255, avg_color[1]/255, avg_color[2]/255)
        s = min(s * 1.5, 1.0)  # Increase saturation by 50%, but not above 1.0
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        
        return (int(r*255), int(g*255), int(b*255))
    except Exception as e:
        print(f"Error getting dominant color from {image_path}: {e}")
        return (128, 128, 128)  # Default to gray on error

# Function to apply color to the background
def apply_color_to_background(background_img, color):
    try:
        # Create a gradient background instead of solid color
        width, height = background_img.size
        
        # Create a new image with the same size and mode
        gradient_bg = Image.new('RGBA', background_img.size, (0, 0, 0, 0))
        
        # Extract the base color components
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
        
        # Create a radial gradient using a more efficient method
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
        gradient_bg = small_gradient.resize(background_img.size, Image.BICUBIC)
        
        # Use the original background's alpha channel as a mask
        if background_img.mode == 'RGBA':
            r, g, b, a = background_img.split()
            gradient_bg.putalpha(a)
            
        return gradient_bg
    except Exception as e:
        print(f"Error applying color to background: {e}")
        return background_img  # Return original background on error

# Function to load local MRKT data as fallback
def load_local_mrkt_data(gift_name):
    """Load price from local gifts_collections.json if API fails"""
    try:
        if 'MRKT_API_DIR' in globals():
            json_path = os.path.join(MRKT_API_DIR, "gifts_collections.json")
        else:
             from config.paths import PROJECT_ROOT
             json_path = os.path.join(PROJECT_ROOT, "api", "mrkt", "gifts_collections.json")
        if not os.path.exists(json_path):
            return None
            
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        # Normalize search name
        target = gift_name.lower().replace("’", "'") # Handle smart quotes
        
        for item in data:
            title = item.get('title', '').lower().replace("’", "'")
            name = item.get('name', '').lower().replace("’", "'")
            
            if title == target or name == target:
                # Found match
                nano_price = item.get('floorPriceNanoTons')
                if nano_price:
                    price_ton = float(nano_price) / 1000000000.0
                    
                    # Get USD price
                    try:
                        from ton_price_utils import get_ton_price_usd
                        ton_price_usd = get_ton_price_usd()
                    except:
                        ton_price_usd = 2.0
                        
                    price_usd = price_ton * ton_price_usd
                    
                    print(f"[Fallback] Found {gift_name} in local MRKT data: {price_ton} TON")
                    return {
                        "name": gift_name,
                        "priceTon": price_ton,
                        "priceUsd": price_usd,
                        "changePercentage": 0,
                        "upgradedSupply": "N/A",
                        "is_fallback": True
                    }
        return None
    except Exception as e:
        print(f"Error loading local MRKT data: {e}")
        return None

# Function to fetch gift price data - updated to use Tonnel API for premarket gifts, Portal API for others
async def fetch_gift_data(gift_name, force_fresh=False):
    """Fetch gift data using appropriate API based on gift type: MRKT/Quant for plus premarket, Tonnel for premarket, Portal for regular."""
    try:
        # Check if this is a plus premarket gift first
        from services.plus_premarket_gifts import is_plus_premarket_gift
        if is_plus_premarket_gift(gift_name):
            if force_fresh:
                print(f"[Plus Premarket] 🔥 FORCE FRESH: Using MRKT/Quant API for {gift_name}")
            else:
                print(f"[Plus Premarket] Using MRKT/Quant API for {gift_name}")
            
            # Use MRKT/Quant API for plus premarket gifts
            import mrkt_quant_api
            gift_data = await mrkt_quant_api.fetch_gift_data(gift_name)
            if gift_data:
                return gift_data
            else:
                print(f"[Plus Premarket] MRKT/Quant API failed for {gift_name}, no fallback available")
                return None
        
        # Check if this is a regular premarket gift (Tonnel API)
        from services import tonnel_api
        # Check if gift_name is one of the values in PREMARKET_GIFTS (display names)
        premarket_key = None
        for key, value in tonnel_api.PREMARKET_GIFTS.items():
            if value == gift_name:
                premarket_key = key
                break
        
        if premarket_key:
            if force_fresh:
                print(f"[Premarket] 🔥 FORCE FRESH: Using Tonnel API for {gift_name} (key: {premarket_key})")
            else:
                print(f"[Premarket] Using Tonnel API for {gift_name} (key: {premarket_key})")
            
            # Use Tonnel API for premarket gifts
            price_ton = await tonnel_api.get_tonnel_gift_price(premarket_key, force_fresh=force_fresh)
            if price_ton:
                # Convert Tonnel API price to proper format
                # Get real TON price from CoinMarketCap
                try:
                    from ton_price_utils import get_ton_price_usd
                    ton_price_usd = get_ton_price_usd()
                except ImportError:
                    ton_price_usd = 2.10  # Fallback value
                price_usd = price_ton * ton_price_usd
                return {
                    "name": gift_name,
                    "priceTon": price_ton,
                    "priceUsd": price_usd,
                    "changePercentage": 0,  # Tonnel API doesn't provide this
                    "upgradedSupply": "N/A"  # Will be filled by supply API
                }
            else:
                print(f"[Premarket] Tonnel API failed for {gift_name}, falling back to Portal API")
                from services.portal_api import fetch_gift_data as portal_fetch
                return await portal_fetch(gift_name, is_premarket=False)
        else:
            if force_fresh:
                print(f"[Regular] 🔥 FORCE FRESH: Using Portal API for {gift_name} (premarket=False)")
            else:
                print(f"[Regular] Using Portal API for {gift_name} (premarket=False)")
            
            # Use Portal API for regular gifts
            from services.portal_api import fetch_gift_data as portal_fetch
            data = await portal_fetch(gift_name, is_premarket=False)
            
            if data:
                return data
            
            # If Portal API failed, try local MRKT data fallback
            print(f"[Fallback] Checking local MRKT JSON for {gift_name}...")
            return load_local_mrkt_data(gift_name)
            
    except Exception as e:
        print(f"Error fetching gift data for {gift_name}: {e}")
        # Try fallback even on exception
        return load_local_mrkt_data(gift_name)

# Function to fetch chart data for a gift - updated to use Legacy API for premarket gifts, Portal API for others
async def fetch_chart_data(gift_name, force_fresh=False):
    """Fetch chart data using appropriate API based on gift type: MRKT/Quant for plus premarket, Legacy API for premarket, Portal API for regular."""
    try:
        # Check if this is a plus premarket gift first
        from services.plus_premarket_gifts import is_plus_premarket_gift
        if is_plus_premarket_gift(gift_name):
            if force_fresh:
                print(f"[Plus Premarket] 🔥 FORCE FRESH: Using MRKT/Quant API for {gift_name} chart data")
            else:
                print(f"[Plus Premarket] Using MRKT/Quant API for {gift_name} chart data")
            
            # Use MRKT/Quant API for plus premarket gifts
            import mrkt_quant_api
            chart_data = await mrkt_quant_api.fetch_chart_data(gift_name)
            if chart_data:
                return chart_data
            else:
                print(f"[Plus Premarket] Chart data not available for {gift_name}")
                return []
        
        # Check if this is a regular premarket gift (Tonnel API)
        from services import tonnel_api
        # Check if gift_name is one of the values in PREMARKET_GIFTS (display names)
        premarket_key = None
        for key, value in tonnel_api.PREMARKET_GIFTS.items():
            if value == gift_name:
                premarket_key = key
                break
        
        if premarket_key:
            if force_fresh:
                print(f"[Premarket] 🔥 FORCE FRESH: Using Legacy API for {gift_name} chart data (key: {premarket_key})")
                # Clear chart cache when forcing fresh
                tonnel_api._chart_cache.clear()
                tonnel_api._cache_timestamp = 0
            else:
                print(f"[Premarket] Using Legacy API for {gift_name} chart data (key: {premarket_key})")
            
            # Use Legacy API for premarket gifts
            chart_data = await tonnel_api.get_tonnel_chart_data(premarket_key, force_fresh=force_fresh)
            if chart_data:
                return chart_data
            else:
                print(f"[Premarket] Legacy API failed for {gift_name} chart, falling back to Portal API")
                from services.portal_api import fetch_chart_data as portal_fetch
                return await portal_fetch(gift_name)
        else:
            if force_fresh:
                print(f"[Regular] 🔥 FORCE FRESH: Using Portal API for {gift_name} chart data (premarket=False)")
            else:
                print(f"[Regular] Using Portal API for {gift_name} chart data (premarket=False)")
            
            # Use Portal API for regular gifts
            from services.portal_api import fetch_chart_data as portal_fetch
            return await portal_fetch(gift_name)
            
    except Exception as e:
        print(f"Error fetching chart data for {gift_name}: {e}")
        return []

# Function to calculate percentage change from chart data
def calculate_percentage_change(chart_data, gift_name=None):
    """
    Calculate the 24-hour percentage change from chart data.
    Uses Legacy API calculation for premarket gifts, Portal API for others.
    
    Args:
        chart_data: List of price data points from API
        gift_name: Name of the gift (used to determine calculation method)
        
    Returns:
        float: Percentage change over exactly 24 hours
    """
    try:
        # Check if this is a premarket gift
        if gift_name:
            from services import tonnel_api
            # Check if gift_name is one of the values in PREMARKET_GIFTS (display names)
            premarket_key = None
            for key, value in tonnel_api.PREMARKET_GIFTS.items():
                if value == gift_name:
                    premarket_key = key
                    break
            
            if premarket_key:
                print(f"[Premarket] Calculating price change for {gift_name} using Legacy API method")
                # Use Legacy API's calculation method for premarket gifts
                return tonnel_api.calculate_percentage_change_from_chart(chart_data)
            else:
                print(f"[Regular] Calculating price change for {gift_name} using Portal API method")
                # Use Portal API's calculation method for regular gifts
                return portal_api.calculate_percentage_change(chart_data)
        else:
            # Default to Portal API method if no gift name provided
            return portal_api.calculate_percentage_change(chart_data)
    except Exception as e:
        print(f"Error calculating percentage change: {e}")
        return 0

def calculate_percentage_change_from_points(start_point, end_point):
    """
    Calculate percentage change between two data points
    
    Args:
        start_point: Starting data point with priceUsd
        end_point: Ending data point with priceUsd
        
    Returns:
        float: Percentage change
    """
    try:
        start_price = float(start_point["priceUsd"])
        end_price = float(end_point["priceUsd"])
        
        if start_price > 0:
            return ((end_price - start_price) / start_price) * 100
        else:
            return 0
    except (KeyError, ValueError, TypeError) as e:
        print(f"Error calculating percentage from points: {e}")
        return 0

# Function to colorize an icon with the gift's color
def colorize_icon(icon_path, color):
    try:
        # Open the icon image
        icon = Image.open(icon_path)
        
        # Convert to RGBA if needed
        if icon.mode != 'RGBA':
            icon = icon.convert('RGBA')
        
        # Create a colored layer
        colored_layer = Image.new('RGBA', icon.size, color + (0,))  # Transparent color
        
        # Create a mask from the icon's alpha channel
        r, g, b, a = icon.split()
        
        # Create a new image with the colored layer and the original alpha
        colored_icon = Image.new('RGBA', icon.size, (0, 0, 0, 0))
        colored_icon.paste(color, (0, 0, icon.width, icon.height), a)
        
        return colored_icon
    except Exception as e:
        print(f"Error colorizing icon {icon_path}: {e}")
        return None

# Function to draw a supply badge showing the number of pieces
def draw_supply_badge(img, supply_count, position=(20, 20), max_width=150):
    """
    Draw a supply badge on the image showing the number of pieces
    
    Args:
        img: The PIL Image to draw on
        supply_count: The number to display
        position: (x, y) coordinates for badge placement
        max_width: Maximum width of the badge
        
    Returns:
        PIL Image with badge drawn on it
    """
    try:
        # Format the supply count with commas
        if isinstance(supply_count, (int, float)) and supply_count >= 1000:
            formatted_supply = f"{supply_count:,}"
        elif isinstance(supply_count, (int, float)):
            formatted_supply = str(supply_count)
        else:
            formatted_supply = str(supply_count)  # e.g. 'N/A'
        
        # Add "pcs" text
        badge_text = f"{formatted_supply} pcs"
        
        # Create a copy of the image to avoid modifying the original
        img_with_badge = img.copy()
        draw = ImageDraw.Draw(img_with_badge)
        
        # Load font for the badge (using a smaller size than the main text)
        try:
            badge_font = ImageFont.truetype(font_path, 24)
        except:
            badge_font = ImageFont.load_default()
        
        # Calculate text size
        text_bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Badge dimensions with padding
        h_padding = 15
        v_padding = 5
        badge_width = min(text_width + h_padding * 2, max_width)
        badge_height = text_height + v_padding * 2
        
        # Badge rounded rectangle coordinates
        x, y = position
        badge_coords = [x, y, x + badge_width, y + badge_height]
        
        # Draw semi-transparent white rounded rectangle
        draw.rounded_rectangle(badge_coords, radius=badge_height//2, 
                              fill=(255, 255, 255, 180))  # Semi-transparent white
        
        # Draw text centered in badge
        text_x = x + (badge_width - text_width) // 2
        text_y = y + (badge_height - text_height) // 2
        draw.text((text_x, text_y), badge_text, font=badge_font, fill=(0, 0, 0, 230))  # Nearly black
        
        return img_with_badge
    except Exception as e:
        print(f"Error drawing supply badge: {e}")
        # Return original image if there's an error
        return img

# Function to generate a chart image from real data
def generate_chart_image(width, height, chart_data, color=(46, 204, 113)):
    try:
        # Create a new transparent image
        chart_img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(chart_img)
        
        # Check if we have data
        if not chart_data:
            print("No chart data available, generating placeholder")
            # Generate some placeholder data
            num_points = 24
            prices = [random.uniform(5000, 15000) for _ in range(num_points)]
        else:
            # Extract prices from the chart data
            prices = [float(point["priceUsd"]) for point in chart_data]
            
        # Determine if price is increasing or decreasing
        price_change = prices[-1] - prices[0]
        price_increased = price_change >= 0
        
        # Set color based on price movement
        if price_increased:
            color = (46, 204, 113)  # Green for price increase
        else:
            color = (231, 76, 60)  # Red for price decrease
        
        # Find min and max prices for scaling
        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price
        
        # Add padding to the price range to avoid chart touching edges
        padding = price_range * 0.1
        adjusted_min = min_price - padding
        adjusted_max = max_price + padding
        adjusted_range = adjusted_max - adjusted_min
        
        # Generate points for the chart
        num_points = len(prices)
        points = []
        
        # Chart dimensions adjustment - extend almost to the right edge
        effective_width = width - 20
        
        # Scale prices to fit chart height
        for i, price in enumerate(prices):
            x = i * (effective_width / (num_points - 1)) if num_points > 1 else effective_width / 2
            # Invert y-axis (higher price = lower y value)
            normalized_price = (price - adjusted_min) / adjusted_range if adjusted_range > 0 else 0.5
            y = height - (normalized_price * height)
            y = max(2, min(height-2, y))  # Keep within bounds
            points.append((x, y))
        
        # Add data points/markers at strategic locations
        marker_points = [0]  # Start point
        
        # Add a few more marker points if we have enough data
        if num_points >= 8:
            marker_points.append(num_points // 4)  # 25% point
            marker_points.append(num_points // 2)  # Middle point
            marker_points.append((num_points * 3) // 4)  # 75% point
        
        marker_points.append(num_points - 1)  # End point
        
        # Draw filled area under the curve first
        fill_points = points.copy()
        fill_points.append((effective_width, height))  # Bottom right
        fill_points.append((0, height))      # Bottom left
        
        # Create a very subtle fill
        fill_color = color + (15,)  # Very subtle transparency
        draw.polygon(fill_points, fill=fill_color)
        
        # Draw line segments connecting the points
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=color, width=7)
        
        # Draw markers at selected points
        marker_size = 7
        for idx in marker_points:
            if idx < len(points):
                x, y = points[idx]
                
                # Draw outer circle
                draw.ellipse((x-marker_size, y-marker_size, x+marker_size, y+marker_size), 
                            fill=(255, 255, 255, 220), outline=color)
                
                # Inner circle with color
                inner_size = marker_size // 2
                draw.ellipse((x-inner_size, y-inner_size, x+inner_size, y+inner_size), 
                            fill=color)
        
        # Add time labels if we have real data
        if chart_data:
            font = ImageFont.truetype(font_path, 18)
            label_color = (120, 120, 120)
            
            # Select a few data points for labels
            label_indices = [0, num_points // 3, (2 * num_points) // 3, num_points - 1]
            
            for idx in label_indices:
                if idx < len(chart_data):
                    time_str = chart_data[idx]["time"]
                    x = points[idx][0]
                    
                    # Center the text on position
                    text_width = draw.textlength(time_str, font=font)
                    draw.text((x - text_width/2, height - 20), time_str, fill=label_color, font=font)
        
        # Add price labels on the right side
        if len(prices) > 0:
            price_font = ImageFont.truetype(font_path, 24)
            price_label_color = (120, 120, 120)
            
            # Define number of price labels (around 6-8 is good)
            num_labels = 7
            
            # Calculate min and max prices to show on the chart
            # Round to nice numbers to make the scale more intuitive
            min_display_price = max(0, math.floor(adjusted_min))
            max_display_price = math.ceil(adjusted_max)
            display_range = max_display_price - min_display_price
            
            # Choose a nice step size that divides the range into approximately num_labels segments
            if display_range > 0:
                # Find a nice step size (1, 2, 5, 10, 20, 25, 50, etc.)
                step_size = 1
                candidates = [1, 2, 5, 10, 20, 25, 50, 100, 200, 500, 1000]
                target_steps = num_labels - 1
                
                for candidate in candidates:
                    if display_range / candidate <= target_steps:
                        step_size = candidate
                        break
                
                # Generate evenly spaced price values
                price_values = []
                current_value = min_display_price
                while current_value <= max_display_price and len(price_values) < num_labels:
                    price_values.append(current_value)
                    current_value += step_size
                
                # If we don't have enough values, add the max price
                if len(price_values) < num_labels:
                    if price_values[-1] < max_display_price:
                        price_values.append(max_display_price)
            else:
                # Fallback for when min and max are the same
                price_values = [min_display_price] * num_labels
            
            # Draw the price labels
            for i, price_value in enumerate(price_values):
                # Calculate normalized position (0 = bottom, 1 = top)
                norm_pos = (price_value - adjusted_min) / adjusted_range if adjusted_range > 0 else 0.5
                # Convert to y position (inverted, 0 = top of chart)
                y_pos = height - (norm_pos * height)
                
                # Format price label as clean integer (no decimals)
                if price_value >= 1000:
                    price_label = f"{int(price_value):,}".replace(",", " ")
                else:
                    price_label = f"{int(price_value)}"
                
                # Draw the label on the right side
                text_width = draw.textlength(price_label, font=price_font)
                draw.text((width - text_width - 5, y_pos - 12), price_label, fill=price_label_color, font=price_font)
        
        return chart_img, price_increased, price_change
    
    except Exception as e:
        print(f"Error generating chart: {e}")
        # Return an empty transparent image if there's an error
        return Image.new('RGBA', (width, height), (255, 255, 255, 0)), True, 0

# Function to create a gift card
async def create_gift_card(gift_name, output_path=None, force_fresh=False):
    """
    Create a gift card for the specified gift name with the new design.
    Uses sticker-style design for plus premarket gifts (no chart data).
    Uses regular gift card design for other gifts.
    
    Args:
        gift_name: The name of the gift to create a card for
        output_path: Optional path to save the card to
        force_fresh: If True, bypass all caches and force fresh API calls
    """
    try:
        # Check if this is a plus premarket gift - use sticker-style design
        from services.plus_premarket_gifts import is_plus_premarket_gift
        if is_plus_premarket_gift(gift_name):
            print(f"Creating plus premarket gift card (sticker style) for: {gift_name}")
            
            # Import plus premarket card generator
            from generators.plus_premarket_card_generator import generate_plus_premarket_card
            import mrkt_quant_api
            
            # Fetch gift data
            gift_data = await mrkt_quant_api.fetch_gift_data(gift_name)
            
            # If gift_data is None or has $0 price, use first_sale_price as fallback
            if not gift_data or gift_data.get('priceUsd', 0) == 0:
                from services.plus_premarket_gifts import get_first_sale_price_stars, get_gift_supply, STAR_TO_USD
                from ton_price_utils import get_ton_price_usd
                
                first_sale_stars = get_first_sale_price_stars(gift_name)
                if first_sale_stars:
                    first_sale_usd = first_sale_stars * STAR_TO_USD
                    ton_price_usd = get_ton_price_usd()
                    first_sale_ton = first_sale_usd / ton_price_usd if ton_price_usd > 0 else 0
                    
                    logger.warning(f"No active listings for {gift_name}, using first sale price: ${first_sale_usd:.2f}")
                    gift_data = {
                        "name": gift_name,
                        "priceUsd": first_sale_usd,
                        "priceTon": first_sale_ton,
                        "changePercentage": 0,
                        "model": "",
                        "backdrop": "",
                        "symbol": "",
                        "upgradedSupply": get_gift_supply(gift_name)
                    }
                else:
                    print(f"Error: Could not fetch data for {gift_name}")
                    return None
            
            # Generate sticker-style card with gift_data (output_path will be handled by the generator)
            card = generate_plus_premarket_card(gift_name, gift_data, output_path)
            return card
        
        # Check if this is a regular premarket gift - use sticker-style design but different API logic
        from services.premarket_gifts import is_premarket_gift, is_transitioned_to_market, get_premarket_supply, get_premarket_first_sale_price_stars, STAR_TO_USD
        if is_premarket_gift(gift_name):
            print(f"Creating premarket gift card (sticker style) for: {gift_name}")
            
            # Check if 21 days have passed - if yes, use Portal API (normal market), if no, use Tonnel API
            transitioned = is_transitioned_to_market(gift_name)
            
            if transitioned:
                print(f"[Premarket] {gift_name} has transitioned to market (21+ days), using Portal API")
                # Use Portal API for normal market gifts
                from services.portal_api import fetch_gift_data as portal_fetch
                gift_data = await portal_fetch(gift_name, is_premarket=False)
            else:
                print(f"[Premarket] {gift_name} is still in premarket (<21 days), using Tonnel API")
                # Use Tonnel API for premarket gifts - need to find the premarket key
                from services import tonnel_api
                premarket_key = None
                for key, value in tonnel_api.PREMARKET_GIFTS.items():
                    if value == gift_name:
                        premarket_key = key
                        break
                
                if premarket_key:
                    price_ton = await tonnel_api.get_tonnel_gift_price(premarket_key, force_fresh=force_fresh)
                    if price_ton:
                        from ton_price_utils import get_ton_price_usd
                        ton_price_usd = get_ton_price_usd()
                        price_usd = price_ton * ton_price_usd
                        gift_data = {
                            "name": gift_name,
                            "priceTon": price_ton,
                            "priceUsd": price_usd,
                            "changePercentage": 0,
                            "upgradedSupply": get_premarket_supply(gift_name)
                        }
                    else:
                        gift_data = None
                else:
                    print(f"[Premarket] Could not find premarket key for {gift_name}")
                    gift_data = None
            
            # Import plus premarket card generator (same design)
            from generators.plus_premarket_card_generator import generate_plus_premarket_card
            from ton_price_utils import get_ton_price_usd
            
            # Ensure gift_data has the correct format for the card generator
            if gift_data and isinstance(gift_data, dict):
                # Normalize gift_data format
                if 'upgradedSupply' not in gift_data:
                    gift_data['upgradedSupply'] = get_premarket_supply(gift_name)
                if 'model' not in gift_data:
                    gift_data['model'] = ""
                if 'backdrop' not in gift_data:
                    gift_data['backdrop'] = ""
                if 'symbol' not in gift_data:
                    gift_data['symbol'] = ""
                if 'changePercentage' not in gift_data:
                    gift_data['changePercentage'] = 0
            
            # If gift_data is None or has $0 price, use first_sale_price as fallback
            if not gift_data or gift_data.get('priceUsd', 0) == 0:
                first_sale_stars = get_premarket_first_sale_price_stars(gift_name)
                if first_sale_stars:
                    first_sale_usd = first_sale_stars * STAR_TO_USD
                    ton_price_usd = get_ton_price_usd()
                    first_sale_ton = first_sale_usd / ton_price_usd if ton_price_usd > 0 else 0
                    
                    logger.warning(f"No active listings for {gift_name}, using first sale price: ${first_sale_usd:.2f}")
                    gift_data = {
                        "name": gift_name,
                        "priceUsd": first_sale_usd,
                        "priceTon": first_sale_ton,
                        "changePercentage": 0,
                        "model": "",
                        "backdrop": "",
                        "symbol": "",
                        "upgradedSupply": get_premarket_supply(gift_name)
                    }
                else:
                    print(f"Error: Could not fetch data for {gift_name}")
                    return None
            
            # Generate sticker-style card with gift_data (same design as +premarket)
            card = generate_plus_premarket_card(gift_name, gift_data, output_path)
            return card
        
        # Regular gift card generation (with chart)
        if force_fresh:
            print(f"🔥 FORCE FRESH MODE: Creating card for {gift_name} with fresh API data")
            # Clear all caches from tonnel_api
            from services import tonnel_api
            tonnel_api.clear_all_caches()
        
        print(f"Creating gift card for: {gift_name}")
        
        # Fetch gift data and chart data concurrently
        print("Fetching gift and chart data...")
        gift_data, chart_data = await asyncio.gather(
            fetch_gift_data(gift_name, force_fresh=force_fresh),
            fetch_chart_data(gift_name, force_fresh=force_fresh)
        )
        
        # Check if files exist
        if not os.path.exists(background_path):
            print(f"Error: Background file not found at {background_path}")
            return None
            
        if not os.path.exists(white_box_path):
            print(f"Error: White box file not found at {white_box_path}")
            return None
            
        if not os.path.exists(font_path):
            print(f"Error: Font file not found at {font_path}")
            return None
            
        # Load background and white box images
        background_img = Image.open(background_path).convert("RGBA")
        white_box_img = Image.open(white_box_path).convert("RGBA")
        
        # Make sure both images are the same size (1600x1000)
        target_size = (1600, 1000)
        background_img = background_img.resize(target_size)
        white_box_img = white_box_img.resize(target_size)
        
        # Find the gift image file
        # Handle special characters in filenames - normalize consistently
        if gift_name == "Jack-in-the-Box":
            normalized_name = "Jack_in_the_Box"
        elif gift_name == "Durov's Cap":
            normalized_name = "Durovs_Cap"
        elif gift_name == "Durov's Statuette":
            normalized_name = "Durovs_Statuette"
        else:
            # Normalize: replace spaces, hyphens, and apostrophes with underscores
            normalized_name = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
        gift_img_path = find_image_file(os.path.join(input_dir, f"{normalized_name}"))
        
        # Check if the file exists, if not try alternative naming patterns
        if not os.path.exists(gift_img_path):
            # Try without underscores (for premarket gifts like SnoopDogg)
            alt_name = gift_name.replace(" ", "").replace("-", "").replace("'", "")
            alt_path = find_image_file(os.path.join(input_dir, alt_name))
            if os.path.exists(alt_path):
                gift_img_path = alt_path
            else:
                # Try original name with just spaces replaced
                alt_name2 = gift_name.replace(" ", "_")
                alt_path2 = find_image_file(os.path.join(input_dir, alt_name2))
                if os.path.exists(alt_path2):
                    gift_img_path = alt_path2
                else:
                    print(f"Error: Image file for {gift_name} not found at {gift_img_path}, {alt_path}, or {alt_path2}")
                    return None
        
        # Get dominant color from gift image
        dominant_color = get_dominant_color(gift_img_path)
        
        # Check if we have a pre-generated background
        safe_name = gift_name.replace(' ', '_').replace('-', '_').replace("'", '')
        pregenerated_bg_path = find_image_file(os.path.join(backgrounds_dir, f"{safe_name}_background"))
        
        if os.path.exists(pregenerated_bg_path):
            # Use the pre-generated background
            colored_background = Image.open(pregenerated_bg_path).convert("RGBA")
            if colored_background.size != background_img.size:
                colored_background = colored_background.resize(background_img.size)
        else:
            # Apply color to the background (fallback)
            colored_background = apply_color_to_background(background_img, dominant_color)
        
        # Create a new blank canvas with the same size
        card = Image.new('RGBA', background_img.size, (0, 0, 0, 0))
        
        # Paste the colored background
        card.paste(colored_background, (0, 0), colored_background if colored_background.mode == 'RGBA' else None)
        
        # Create shadow for white box
        shadow_offset = 5
        shadow_blur = 10
        shadow_opacity = 40
        
        # Create a shadow layer
        shadow = Image.new('RGBA', background_img.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        
        # Calculate center position for white box
        box_width, box_height = white_box_img.size
        x_center = (background_img.width - box_width) // 2
        y_center = (background_img.height - box_height) // 2
        
        # Create a blurred black rectangle for the shadow
        shadow_rect = (
            x_center + shadow_offset, 
            y_center + shadow_offset, 
            x_center + box_width + shadow_offset, 
            y_center + box_height + shadow_offset
        )
        shadow_draw.rectangle(shadow_rect, fill=(0, 0, 0, shadow_opacity))
        
        # Apply blur to the shadow
        shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))
        
        # Ensure card is RGBA before alpha_composite
        if card.mode != 'RGBA':
            card = card.convert('RGBA')
        if shadow.mode != 'RGBA':
            shadow = shadow.convert('RGBA')
            
        # Composite the shadow onto the card
        card = Image.alpha_composite(card, shadow)
        
        # Paste the white box on top at the center position
        card.paste(white_box_img, (x_center, y_center), white_box_img if white_box_img.mode == 'RGBA' else None)
        
        # Open the gift image
        gift_img = Image.open(gift_img_path)
        
        # Convert to RGBA if needed
        if gift_img.mode != 'RGBA':
            gift_img = gift_img.convert('RGBA')
            
        # Resize gift image to match reference (slightly larger)
        gift_img.thumbnail((150, 150))  # Increased size for better visibility
        
        # Position for the gift image - adjusting to be properly inside the white box
        gift_x = x_center + 150  # Moved 5px to the right
        gift_y = y_center + 130  # Better centered in the white box
        
        # Apply a subtle highlight effect to the gift image
        enhancer = ImageEnhance.Brightness(gift_img)
        gift_img = enhancer.enhance(1.05)  # Subtle brightness boost
        
        # Paste the gift image onto the card
        card.paste(gift_img, (gift_x, gift_y), gift_img)
        
        # Prepare for drawing text
        draw = ImageDraw.Draw(card)
        
        # Draw gift name with independent positioning
        name_font = ImageFont.truetype(font_path, 100)
        name_color = (60, 60, 60)
        name_x = x_center + 310
        name_y = y_center + 150
        draw.text((name_x, name_y), gift_name, fill=name_color, font=name_font)
        
        # Get price from API data or handle unavailable prices
        current_price_usd = 0
        current_price_ton = 0
        price_unavailable = False
        
        if gift_data:
            if gift_data.get("priceUnavailable"):
                price_unavailable = True
                print(f"[Warning] Price unavailable for {gift_name} - will show 'Price unavailable'")
            elif "priceUsd" in gift_data and "priceTon" in gift_data:
                if gift_data["priceUsd"] is not None and gift_data["priceTon"] is not None:
                    current_price_usd = float(gift_data["priceUsd"])
                    current_price_ton = float(gift_data["priceTon"])
                else:
                    price_unavailable = True
            else:
                # No price data available
                current_price_usd = random.randint(5000, 50000)
                current_price_ton = current_price_usd / 3.2  # Approximate TON price
        else:
            current_price_usd = random.randint(5000, 50000)
            current_price_ton = current_price_usd / 3.2  # Approximate TON price
        
        # Calculate price in Telegram Stars (1 Star = $0.016)
        if not price_unavailable:
            stars_price = int(current_price_usd / 0.016)
        else:
            stars_price = 0
        
        # Calculate percentage change using the dedicated function
        change_pct = 0
        if gift_data and "changePercentage" in gift_data:
            change_pct = float(gift_data["changePercentage"])
        else:
            # Use our new function to calculate the percentage change
            change_pct = calculate_percentage_change(chart_data)
        
        # Determine color based on percentage change
        change_sign = "+" if change_pct >= 0 else ""
        
        # Create more vibrant colors for change percentage
        if change_pct >= 0:
            change_color = (46, 204, 113)  # Vibrant green
        else:
            change_color = (231, 76, 60)  # Vibrant red
        
        # Draw percentage change at fixed position independent of gift image
        pct_font = ImageFont.truetype(font_path, 70)
        pct_text = f"{change_sign}{int(change_pct)}%"
        pct_width = draw.textlength(pct_text, font=pct_font)
        # Fixed position at top right of white box
        pct_x = x_center + box_width - pct_width - 140
        pct_y = y_center + 155  # Moved down by 5px from 150
        draw.text((pct_x, pct_y), pct_text, fill=change_color, font=pct_font)
        
        # Draw dollar sign and USD price at exact position from reference
        price_font = ImageFont.truetype(font_path, 140)
        dollar_color = dominant_color  # Use the gift's dominant color for the dollar sign
        price_color = (20, 20, 20)
        
        # Position for the dollar sign - matching reference
        dollar_x = x_center + 180
        dollar_y = y_center + 280  # Moved down by 5px from 230
        
        # Draw dollar sign and USD price or unavailable message
        if not price_unavailable:
            draw.text((dollar_x, dollar_y), "$", fill=dollar_color, font=price_font)
            draw.text((dollar_x + 100, dollar_y), f"{current_price_usd:,.0f}".replace(",", " "), fill=price_color, font=price_font)
        else:
            # Show "Price unavailable" message instead
            unavailable_font = ImageFont.truetype(font_path, 80)
            unavailable_text = "Price unavailable"
            unavailable_color = (150, 150, 150)  # Gray color
            draw.text((dollar_x, dollar_y + 30), unavailable_text, fill=unavailable_color, font=unavailable_font)
        
        # Load and colorize TON logo
        ton_logo = Image.open(ton_logo_path)
        if ton_logo.mode != 'RGBA':
            ton_logo = ton_logo.convert('RGBA')
        
        # Resize TON logo to match reference - making it larger
        ton_logo.thumbnail((70, 70))  # Increased from 50x50
        
        # Colorize TON logo with gift's dominant color
        ton_logo_colored = Image.new('RGBA', ton_logo.size, (0, 0, 0, 0))
        for y in range(ton_logo.height):
            for x in range(ton_logo.width):
                r, g, b, a = ton_logo.getpixel((x, y))
                if a > 0:  # If not fully transparent
                    # Replace black with the dominant color, keeping alpha
                    ton_logo_colored.putpixel((x, y), dominant_color + (a,))
        
        # Load and colorize Star logo
        star_logo = Image.open(star_logo_path)
        if star_logo.mode != 'RGBA':
            star_logo = star_logo.convert('RGBA')
        
        # Resize Star logo to match reference - making it larger
        star_logo.thumbnail((70, 70))  # Increased from 50x50
        
        # Colorize Star logo with gift's dominant color
        star_logo_colored = Image.new('RGBA', star_logo.size, (0, 0, 0, 0))
        for y in range(star_logo.height):
            for x in range(star_logo.width):
                r, g, b, a = star_logo.getpixel((x, y))
                if a > 0:  # If not fully transparent
                    # Replace black with the dominant color, keeping alpha
                    star_logo_colored.putpixel((x, y), dominant_color + (a,))
        
        # Position and draw TON, Star logos and prices at exact positions from reference
        ton_y = y_center + 480  # Moved up by 5px from 500
        
        # Increase font size for currency values
        ton_price_font = ImageFont.truetype(font_path, 50)  # Increased from 60
        
        # TON logo and price - vertically center the value with logo
        # Calculate logo center point
        ton_logo_center_y = (ton_y - 15) + (ton_logo.height // 2)
        # Move text up more to properly center with logo
        text_center_offset = ton_price_font.size // 2  # Increased offset to move text up
        
        # Position text to align with the center of the logo
        ton_text_y = ton_logo_center_y - text_center_offset
        
        card.paste(ton_logo_colored, (dollar_x, ton_y - 15), ton_logo_colored)
        
        # Get the width of the TON value text for centering
        ton_text_width = draw.textlength(f"{current_price_ton:.1f}".replace(".", ",").replace(",0", ""), font=ton_price_font)
        
        # Position TON value closer to the logo and vertically centered (only if price available)
        if not price_unavailable:
            ton_text_x = dollar_x + 80  # Reduced separation
            draw.text((ton_text_x, ton_text_y), f"{current_price_ton:.1f}".replace(".", ",").replace(",0", ""), fill=price_color, font=ton_price_font)
            
            # Dot separator - matching reference but moved up
            dot_y = ton_logo_center_y  # Center the dot vertically
            # Calculate position for dot to be centered between TON and Star values
            dot_x = int(ton_text_x + ton_text_width + 30)  # Reduced spacing from 60 to 30
            draw.ellipse((dot_x - 7, dot_y - 7, dot_x + 8, dot_y + 8), fill=(100, 100, 100))
            
            # Star logo and price - vertically center the value with logo
            star_x = int(dot_x + 20)  # Reduced spacing after dot (was 40)
            card.paste(star_logo_colored, (star_x, ton_y - 15), star_logo_colored)
            
            # Position Star value closer to the logo and vertically centered
            star_text_x = star_x + 80  # Reduced separation
            draw.text((star_text_x, ton_text_y), f"{stars_price:,}".replace(",", " "), fill=price_color, font=ton_price_font)
        
        # Dimensions and positioning for the chart - matching reference exactly
        chart_width = 1300
        chart_height = 240
        
        # Generate chart from real data
        chart_img, price_increased, price_change = generate_chart_image(chart_width, chart_height, chart_data, color=change_color)
        
        # Position the chart at the bottom of the white box - moved down
        chart_x = x_center + 150
        chart_y = y_center + 590  # Moved down by additional 20px
        
        # Paste the chart
        card.paste(chart_img, (chart_x, chart_y), chart_img)
        
        # Add timestamp under the chart
        current_time = datetime.datetime.now().strftime("%d %b %Y • %H:%M UTC")
        timestamp_font = ImageFont.truetype(font_path, 24)
        timestamp_color = (120, 120, 120)
        
        # Calculate text width for centering
        timestamp_width = draw.textlength(current_time, font=timestamp_font)
        timestamp_x = chart_x + (chart_width - timestamp_width) // 2
        timestamp_y = chart_y + chart_height + 15  # Position below the chart
        
        # Draw the timestamp
        draw.text((timestamp_x, timestamp_y), current_time, fill=timestamp_color, font=timestamp_font)
        
        # Only add supply badge when upgradedSupply data is available and is a positive number
        supply_count = "N/A"
        if gift_data and "upgradedSupply" in gift_data:
            supply_count = gift_data["upgradedSupply"]
            
        if supply_count != "N/A" and isinstance(supply_count, (int, float)) and supply_count > 0:
            try:
                # Get gift image path - handle premarket gifts differently
                from services import tonnel_api
                is_premarket = False
                for key, value in tonnel_api.PREMARKET_GIFTS.items():
                    if value == gift_name:
                        is_premarket = True
                        break
                
                if is_premarket:
                    # For premarket gifts, use the display name with underscores (e.g., "Clover_Pin.webp")
                    normalized_name = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
                    gift_image_path = find_image_file(os.path.join(input_dir, normalized_name))
                else:
                    # For regular gifts, use the display name with underscores
                    normalized_name = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
                    gift_image_path = find_image_file(os.path.join(input_dir, normalized_name))
                
                # If gift image exists, add badge to it
                if os.path.exists(gift_image_path):
                    # Load gift image
                    gift_img = Image.open(gift_image_path).convert("RGBA")
                    
                    # Calculate gift image size
                    gift_size = 150  # Based on the thumbnail size
                    if gift_img.width > gift_size or gift_img.height > gift_size:
                        gift_img.thumbnail((gift_size, gift_size))
                    
                    # Create badge with supply count
                    gift_img_with_badge = draw_supply_badge(gift_img, supply_count, 
                                                           position=(10, 120))
                    
                    # Gift position (matches the one used earlier in the function)
                    gift_pos_x = gift_x
                    gift_pos_y = gift_y
                    
                    # Paste gift with badge onto card 
                    card.paste(gift_img_with_badge, (gift_pos_x, gift_pos_y), gift_img_with_badge)
            except Exception as e:
                print(f"Error adding supply badge: {e}")
        
        # Add watermark at top center
        watermark_lines = ["@GiftsChartbot"]
        watermark_font = ImageFont.truetype(font_path, 32)
        watermark_color = (255, 255, 255, 200)  # Semi-transparent white
        line_height = watermark_font.getbbox("A")[3] + 5
        watermark_y = 30  # Start position
        
        # Draw each line centered
        for i, line in enumerate(watermark_lines):
            line_width = draw.textlength(line, font=watermark_font)
            watermark_x = card.width // 2 - line_width // 2
            line_y = watermark_y + (i * line_height)
            draw.text((watermark_x, line_y), line, fill=watermark_color, font=watermark_font)
        
        # Save the card if output path is provided
        if output_path:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            # Convert output path to WebP if it's PNG
            if output_path.endswith('.png'):
                output_path = output_path[:-4] + '.webp'
            card.save(output_path, 'WEBP', quality=85, method=6)
            
        return card
    
    except Exception as e:
        print(f"Error creating card for {gift_name}: {e}")
        return None

# Function to generate a specific gift card
def generate_specific_gift(gift_name, filename_suffix=""):
    """Generate a price card for a specific gift name."""
    print(f"Processing {gift_name}...")
    
    # Handle special characters in filenames
    if gift_name == "Jack-in-the-Box":
        normalized_name = "Jack_in_the_Box"
    elif gift_name == "Durov's Cap":
        normalized_name = "Durovs_Cap"
    else:
        # General normalization for other names
        normalized_name = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
    
    # Define output path
    output_path = os.path.join(output_dir, f"{normalized_name}{filename_suffix}_card.webp")
    
    try:
        # Check if template exists
        template_path = find_image_file(os.path.join("card_templates", f"{normalized_name}_template"))
        if not os.path.exists(template_path):
            # Generate the template if it doesn't exist
            template_path = generate_template_card(gift_name)
            if not template_path:
                # Fall back to the old method if template generation fails
                print(f"Falling back to full generation for {gift_name}")
                card = asyncio.run(create_gift_card(gift_name, output_path))
                if card:
                    print(f"Saved card to {output_path} (full generation)")
                    return output_path
        
        # Use the optimized method with template
        card = asyncio.run(add_dynamic_elements(gift_name, template_path, output_path))
        if card:
            print(f"Saved card to {output_path} (template-based)")
            return output_path
        
        # Fall back to the old method if the optimized method fails
        print(f"Falling back to full generation for {gift_name}")
        card = asyncio.run(create_gift_card(gift_name, output_path))
        if card:
            print(f"Saved card to {output_path} (full generation)")
            return output_path
        
        return None
    except Exception as e:
        print(f"Error generating card for {gift_name}: {e}")
        # Try the old method as a fallback
        try:
            card = create_gift_card(gift_name, output_path)
            if card:
                print(f"Saved card to {output_path} (fallback full generation)")
                return output_path
        except:
            pass
        return None

# This module is imported by other files for its functions

# Function to generate a template card with all static elements
def generate_template_card(gift_name):
    """Generate a template card with all static elements for a gift."""
    try:
        # Normalize gift name for file system compatibility
        if gift_name == "Jack-in-the-Box":
            normalized_name = "Jack_in_the_Box"
        elif gift_name == "Durov's Cap":
            normalized_name = "Durovs_Cap"
        else:
            normalized_name = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
        
        # Define the template path
        template_dir = "card_templates"
        os.makedirs(template_dir, exist_ok=True)
        template_path = os.path.join(template_dir, f"{normalized_name}_template.webp")
        
        # Check if the template already exists
        if os.path.exists(template_path):
            print(f"Template already exists for {gift_name}")
            return template_path
            
        # Load background and white box images
        background_img = Image.open(background_path).convert("RGBA")
        white_box_img = Image.open(white_box_path).convert("RGBA")
        
        # Make sure both images are the same size (1600x1000)
        target_size = (1600, 1000)
        background_img = background_img.resize(target_size)
        white_box_img = white_box_img.resize(target_size)
        
        # Find the gift image file
        gift_img_path = find_image_file(os.path.join(input_dir, normalized_name))
        
        # Check if the file exists, if not try alternative naming patterns
        if not os.path.exists(gift_img_path):
            # Try without underscores (for premarket gifts like SnoopDogg)
            alt_name = gift_name.replace(" ", "")
            alt_path = find_image_file(os.path.join(input_dir, alt_name))
            if os.path.exists(alt_path):
                gift_img_path = alt_path
            else:
                print(f"Error: Image file for {gift_name} not found at {gift_img_path} or {alt_path}")
                return None
        
        # Get dominant color from gift image
        dominant_color = get_dominant_color(gift_img_path)
        
        # Check if we have a pre-generated background
        pregenerated_bg_path = find_image_file(os.path.join(backgrounds_dir, f"{normalized_name}_background"))
        
        if os.path.exists(pregenerated_bg_path):
            # Use the pre-generated background
            colored_background = Image.open(pregenerated_bg_path).convert("RGBA")
            if colored_background.size != background_img.size:
                colored_background = colored_background.resize(background_img.size)
        else:
            # Apply color to the background (fallback)
            colored_background = apply_color_to_background(background_img, dominant_color)
        
        # Create a new blank canvas with the same size
        template = Image.new('RGBA', background_img.size, (0, 0, 0, 0))
        
        # Paste the colored background
        template.paste(colored_background, (0, 0), colored_background if colored_background.mode == 'RGBA' else None)
        
        # Create shadow for white box
        shadow_offset = 5
        shadow_blur = 10
        shadow_opacity = 40
        
        # Create a shadow layer
        shadow = Image.new('RGBA', background_img.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        
        # Calculate center position for white box
        box_width, box_height = white_box_img.size
        x_center = (background_img.width - box_width) // 2
        y_center = (background_img.height - box_height) // 2
        
        # Create a blurred black rectangle for the shadow
        shadow_rect = (
            x_center + shadow_offset, 
            y_center + shadow_offset, 
            x_center + box_width + shadow_offset, 
            y_center + box_height + shadow_offset
        )
        shadow_draw.rectangle(shadow_rect, fill=(0, 0, 0, shadow_opacity))
        
        # Apply blur to the shadow
        shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))
        
        # Composite the shadow onto the template
        template = Image.alpha_composite(template, shadow)
        
        # Paste the white box on top at the center position
        template.paste(white_box_img, (x_center, y_center), white_box_img if white_box_img.mode == 'RGBA' else None)
        
        # Open the gift image
        gift_img = Image.open(gift_img_path)
        
        # Convert to RGBA if needed
        if gift_img.mode != 'RGBA':
            gift_img = gift_img.convert('RGBA')
            
        # Resize gift image to match reference
        gift_img.thumbnail((150, 150))
        
        # Position for the gift image
        gift_x = x_center + 150
        gift_y = y_center + 130
        
        # Apply a subtle highlight effect to the gift image
        enhancer = ImageEnhance.Brightness(gift_img)
        gift_img = enhancer.enhance(1.05)
        
        # Paste the gift image onto the template
        template.paste(gift_img, (gift_x, gift_y), gift_img)
        
        # Prepare for drawing text
        draw = ImageDraw.Draw(template)
        
        # Draw gift name with independent positioning
        name_font = ImageFont.truetype(font_path, 100)
        name_color = (60, 60, 60)
        name_x = x_center + 310
        name_y = y_center + 150
        draw.text((name_x, name_y), gift_name, fill=name_color, font=name_font)
        
        # Load and colorize TON logo
        ton_logo = Image.open(ton_logo_path)
        if ton_logo.mode != 'RGBA':
            ton_logo = ton_logo.convert('RGBA')
        
        # Resize TON logo
        ton_logo.thumbnail((70, 70))
        
        # Colorize TON logo with gift's dominant color
        ton_logo_colored = Image.new('RGBA', ton_logo.size, (0, 0, 0, 0))
        for y in range(ton_logo.height):
            for x in range(ton_logo.width):
                r, g, b, a = ton_logo.getpixel((x, y))
                if a > 0:
                    ton_logo_colored.putpixel((x, y), dominant_color + (a,))
        
        # Load and colorize Star logo
        star_logo = Image.open(star_logo_path)
        if star_logo.mode != 'RGBA':
            star_logo = star_logo.convert('RGBA')
        
        # Resize Star logo
        star_logo.thumbnail((70, 70))
        
        # Colorize Star logo with gift's dominant color
        star_logo_colored = Image.new('RGBA', star_logo.size, (0, 0, 0, 0))
        for y in range(star_logo.height):
            for x in range(star_logo.width):
                r, g, b, a = star_logo.getpixel((x, y))
                if a > 0:
                    star_logo_colored.putpixel((x, y), dominant_color + (a,))
        
        # Position for TON logo
        ton_y = y_center + 480
        dollar_x = x_center + 180
        
        # Paste TON logo
        template.paste(ton_logo_colored, (dollar_x, ton_y - 15), ton_logo_colored)
        
        # Position for Star logo
        dot_y = (ton_y - 15) + (ton_logo.height // 2)
        ton_text_x = dollar_x + 80
        ton_price_font = ImageFont.truetype(font_path, 50)
        dummy_ton_text = "999.9"  # Placeholder for width calculation
        ton_text_width = draw.textlength(dummy_ton_text, font=ton_price_font)
        dot_x = int(ton_text_x + ton_text_width + 30)
        star_x = int(dot_x + 20)
        
        # Paste Star logo
        template.paste(star_logo_colored, (star_x, ton_y - 15), star_logo_colored)
        
        # Add watermark at top center
        watermark_lines = ["@GiftsChartbot"]
        watermark_font = ImageFont.truetype(font_path, 32)
        watermark_color = (255, 255, 255, 200)  # Semi-transparent white
        line_height = watermark_font.getbbox("A")[3] + 5
        watermark_y = 30  # Start position
        
        # Draw each line centered
        for i, line in enumerate(watermark_lines):
            line_width = draw.textlength(line, font=watermark_font)
            watermark_x = template.width // 2 - line_width // 2
            line_y = watermark_y + (i * line_height)
            draw.text((watermark_x, line_y), line, fill=watermark_color, font=watermark_font)
        
        # Save the template as WebP
        if template_path.endswith('.webp'):
            template_path = template_path[:-4] + '.webp'
        template.save(template_path, 'WEBP', quality=85, method=6)
        print(f"Generated template for {gift_name} at {template_path}")
        
        # Store metadata about the template
        metadata = {
            "gift_name": gift_name,
            "x_center": x_center,
            "y_center": y_center,
            "box_width": box_width,
            "box_height": box_height,
            "dominant_color": dominant_color,
            "dollar_x": dollar_x,
            "dollar_y": y_center + 280,
            "ton_logo_pos": (dollar_x, ton_y - 15),
            "ton_text_pos": (ton_text_x, (ton_y - 15) + (ton_logo.height // 2) - ton_price_font.size // 2),
            "star_logo_pos": (star_x, ton_y - 15),
            "star_text_pos": (star_x + 80, (ton_y - 15) + (ton_logo.height // 2) - ton_price_font.size // 2),
            "chart_pos": (x_center + 150, y_center + 590),
            "chart_size": (1300, 240)
        }
        
        # Save metadata
        metadata_dir = "card_metadata"
        os.makedirs(metadata_dir, exist_ok=True)
        with open(os.path.join(metadata_dir, f"{normalized_name}_metadata.json"), 'w') as f:
            json.dump(metadata, f)
        
        return template_path
        
    except Exception as e:
        print(f"Error generating template for {gift_name}: {e}")
        return None

# Function to add dynamic elements to a template
async def add_dynamic_elements(gift_name, template_path=None, output_path=None):
    """Add dynamic elements (prices, chart) to a template card."""
    try:
        # Normalize gift name for file system compatibility
        if gift_name == "Jack-in-the-Box":
            normalized_name = "Jack_in_the_Box"
        elif gift_name == "Durov's Cap":
            normalized_name = "Durovs_Cap"
        else:
            normalized_name = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
        
        # If no template path provided, use the default one
        if not template_path:
            template_path = find_image_file(os.path.join("card_templates", f"{normalized_name}_template"))
        
        # If template doesn't exist, generate it
        if not os.path.exists(template_path):
            template_path = generate_template_card(gift_name)
            if not template_path:
                return None
        
        # Load the template
        card = Image.open(template_path).convert("RGBA")
        
        # Load metadata
        metadata_path = os.path.join("card_metadata", f"{normalized_name}_metadata.json")
        if not os.path.exists(metadata_path):
            print(f"Error: Metadata not found for {gift_name}")
            return None
            
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Extract needed values
        x_center = metadata["x_center"]
        y_center = metadata["y_center"]
        box_width = metadata["box_width"]
        dominant_color = tuple(metadata["dominant_color"])
        dollar_x = metadata["dollar_x"]
        dollar_y = metadata["dollar_y"]
        
        # Fetch real data for the gift using async Portal API
        gift_data = await fetch_gift_data(gift_name)
        chart_data = await fetch_chart_data(gift_name)
        
        # Get price from API data or handle unavailable prices
        current_price_usd = 0
        current_price_ton = 0
        price_unavailable = False
        supply_count = "N/A"
        
        if gift_data:
            # Get supply data if available
            if "upgradedSupply" in gift_data:
                supply_count = gift_data["upgradedSupply"]
                
            if gift_data.get("priceUnavailable"):
                price_unavailable = True
                print(f"[Warning] Price unavailable for {gift_name} - will show 'Price unavailable'")
            elif "priceUsd" in gift_data and "priceTon" in gift_data:
                if gift_data["priceUsd"] is not None and gift_data["priceTon"] is not None:
                    current_price_usd = float(gift_data["priceUsd"])
                    current_price_ton = float(gift_data["priceTon"])
                else:
                    price_unavailable = True
            else:
                # No price data available
                current_price_usd = random.randint(5000, 50000)
                current_price_ton = current_price_usd / 3.2  # Approximate TON price
        else:
            current_price_usd = random.randint(5000, 50000)
            current_price_ton = current_price_usd / 3.2  # Approximate TON price
        
        # Calculate price in Telegram Stars (1 Star = $0.016)
        if not price_unavailable:
            stars_price = int(current_price_usd / 0.016)
        else:
            stars_price = 0
        
        # Calculate percentage change using the dedicated function
        change_pct = 0
        if gift_data and "changePercentage" in gift_data:
            change_pct = float(gift_data["changePercentage"])
        else:
            # Use our new function to calculate the percentage change
            change_pct = calculate_percentage_change(chart_data, gift_name)
        
        # Determine color based on percentage change
        change_sign = "+" if change_pct >= 0 else ""
        if change_pct >= 0:
            change_color = (46, 204, 113)  # Vibrant green
        else:
            change_color = (231, 76, 60)  # Vibrant red
        
        # Prepare for drawing
        draw = ImageDraw.Draw(card)
        
        # Draw percentage change
        pct_font = ImageFont.truetype(font_path, 70)
        pct_text = f"{change_sign}{int(change_pct)}%"
        pct_width = draw.textlength(pct_text, font=pct_font)
        pct_x = x_center + box_width - pct_width - 140
        pct_y = y_center + 155
        draw.text((pct_x, pct_y), pct_text, fill=change_color, font=pct_font)
        
        # Draw dollar sign and USD price
        price_font = ImageFont.truetype(font_path, 140)
        if not price_unavailable:
            draw.text((dollar_x, dollar_y), "$", fill=dominant_color, font=price_font)
            draw.text((dollar_x + 100, dollar_y), f"{current_price_usd:,.0f}".replace(",", " "), fill=(20, 20, 20), font=price_font)
            
            # Draw TON and Stars prices
            ton_price_font = ImageFont.truetype(font_path, 50)
            draw.text(metadata["ton_text_pos"], f"{current_price_ton:.1f}".replace(".", ",").replace(",0", ""), fill=(20, 20, 20), font=ton_price_font)
            
            # Draw dot separator
            dot_y = metadata["ton_logo_pos"][1] + 35  # Center of logo
            ton_text_width = draw.textlength(f"{current_price_ton:.1f}".replace(".", ",").replace(",0", ""), font=ton_price_font)
            dot_x = int(metadata["ton_text_pos"][0] + ton_text_width + 30)
            draw.ellipse((dot_x - 7, dot_y - 7, dot_x + 8, dot_y + 8), fill=(100, 100, 100))
            
            # Draw Stars price
            draw.text(metadata["star_text_pos"], f"{stars_price:,}".replace(",", " "), fill=(20, 20, 20), font=ton_price_font)
        else:
            # Show "Price unavailable" message
            unavailable_font = ImageFont.truetype(font_path, 80)
            unavailable_text = "Price unavailable"
            unavailable_color = (150, 150, 150)  # Gray color
            
            # Center the text where the price would be
            unavailable_width = draw.textlength(unavailable_text, font=unavailable_font)
            unavailable_x = dollar_x + ((metadata["star_text_pos"][0] + 200 - dollar_x) - unavailable_width) // 2
            unavailable_y = dollar_y + 30  # Slightly lower than main price
            
            draw.text((unavailable_x, unavailable_y), unavailable_text, fill=unavailable_color, font=unavailable_font)
        
        # Generate chart
        chart_width, chart_height = metadata["chart_size"]
        chart_img, _, _ = generate_chart_image(chart_width, chart_height, chart_data, color=change_color)
        
        # Paste chart
        chart_x, chart_y = metadata["chart_pos"]
        card.paste(chart_img, (chart_x, chart_y), chart_img)
        
        # Add timestamp
        current_time = datetime.datetime.now().strftime("%d %b %Y • %H:%M UTC")
        timestamp_font = ImageFont.truetype(font_path, 24)
        timestamp_color = (120, 120, 120)
        timestamp_width = draw.textlength(current_time, font=timestamp_font)
        timestamp_x = chart_x + (chart_width - timestamp_width) // 2
        timestamp_y = chart_y + chart_height + 15
        draw.text((timestamp_x, timestamp_y), current_time, fill=timestamp_color, font=timestamp_font)
        
        # Only add supply badge when upgradedSupply data is available and is a positive number
        if supply_count != "N/A" and isinstance(supply_count, (int, float)) and supply_count > 0:
            try:
                # Get gift image path - handle premarket gifts differently
                from services import tonnel_api
                is_premarket = False
                for key, value in tonnel_api.PREMARKET_GIFTS.items():
                    if value == gift_name:
                        is_premarket = True
                        break
                
                if is_premarket:
                    # For premarket gifts, use the display name with underscores (e.g., "Clover_Pin.webp")
                    normalized_name = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
                    gift_image_path = find_image_file(os.path.join(input_dir, normalized_name))
                else:
                    # For regular gifts, use the display name with underscores
                    normalized_name = gift_name.replace(" ", "_").replace("-", "_").replace("'", "")
                    gift_image_path = find_image_file(os.path.join(input_dir, normalized_name))
                
                # If gift image exists, add badge to it
                if os.path.exists(gift_image_path):
                    # Load gift image
                    gift_img = Image.open(gift_image_path).convert("RGBA")
                    
                    # Calculate gift image size
                    gift_size = 150  # Based on the thumbnail size in generate_template_card
                    if gift_img.width > gift_size or gift_img.height > gift_size:
                        gift_img.thumbnail((gift_size, gift_size))
                    
                    # Create badge with supply count (only if available)
                    gift_img_with_badge = draw_supply_badge(gift_img, supply_count, 
                                                           position=(10, 120))
                    
                    # Gift position (matches the one in generate_template_card)
                    gift_pos_x = x_center + 150
                    gift_pos_y = y_center + 130
                    
                    # Paste gift with badge onto card 
                    card.paste(gift_img_with_badge, (gift_pos_x, gift_pos_y), gift_img_with_badge)
            except Exception as e:
                print(f"Error adding supply badge: {e}")
        
        # Add watermark at top center
        watermark_lines = ["@GiftsChartbot"]
        watermark_font = ImageFont.truetype(font_path, 32)
        watermark_color = (255, 255, 255, 200)  # Semi-transparent white
        line_height = watermark_font.getbbox("A")[3] + 5
        watermark_y = 30  # Start position
        
        # Draw each line centered
        for i, line in enumerate(watermark_lines):
            line_width = draw.textlength(line, font=watermark_font)
            watermark_x = card.width // 2 - line_width // 2
            line_y = watermark_y + (i * line_height)
            draw.text((watermark_x, line_y), line, fill=watermark_color, font=watermark_font)
        
        # Save the final card
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            # Convert output path to WebP if it's PNG
            if output_path.endswith('.png'):
                output_path = output_path[:-4] + '.webp'
            card.save(output_path, 'WEBP', quality=85, method=6)
            
        return card
        
    except Exception as e:
        print(f"Error adding dynamic elements for {gift_name}: {e}")
        return None

# Add this function after the create_gift_card function

def create_custom_card(image_path, output_path, name, price_usd, price_ton, change_percentage, chart_data, force_color=None):
    """
    Create a custom gift card with specified values
    
    Args:
        image_path: Path to the gift image
        output_path: Where to save the resulting card
        name: Name to display on the card
        price_usd: Fixed price in USD
        price_ton: Fixed price in TON
        change_percentage: Fixed change percentage
        chart_data: Custom chart data
        force_color: Optional RGB tuple to force a specific color
    """
    try:
        # Open template elements
        background = Image.open(background_path).convert("RGBA")
        white_box = Image.open(white_box_path).convert("RGBA")
        ton_logo = Image.open(ton_logo_path).convert("RGBA")
        star_logo = Image.open(star_logo_path).convert("RGBA")
        
        # Load the gift image
        if os.path.exists(image_path):
            gift_image = Image.open(image_path).convert("RGBA")
        else:
            print(f"Error: Gift image not found at {image_path}")
            return None
            
        # Get color from image or use forced color
        if force_color:
            dominant_color = force_color
        else:
            dominant_color = get_dominant_color(image_path)
        
        # Create colored background
        colored_bg = apply_color_to_background(background, dominant_color)
        
        # Create card base
        card_width, card_height = 600, 800
        card = Image.new("RGBA", (card_width, card_height), (0, 0, 0, 0))
        
        # Create chart image with price data
        chart_image = generate_chart_image(500, 200, chart_data, color=force_color if force_color else dominant_color)
        
        # Resize gift icon as needed to fit properly
        max_icon_size = 400
        icon_size = min(gift_image.width, gift_image.height, max_icon_size)
        if gift_image.width > gift_image.height:
            icon_height = icon_size
            icon_width = int(gift_image.width * (icon_height / gift_image.height))
        else:
            icon_width = icon_size
            icon_height = int(gift_image.height * (icon_width / gift_image.width))
        
        gift_image = gift_image.resize((icon_width, icon_height), Image.LANCZOS)
        
        # Position elements
        # Background
        card.paste(colored_bg, (0, 0), colored_bg)
        
        # White box
        white_box_position = (30, 150)
        card.paste(white_box, white_box_position, white_box)
        
        # Gift image (centered horizontally, top part of card)
        icon_pos_x = (card_width - icon_width) // 2
        icon_pos_y = 60
        card.paste(gift_image, (icon_pos_x, icon_pos_y), gift_image)
        
        # Draw on the card
        draw = ImageDraw.Draw(card)
        
        # Load fonts
        price_font_size = 48
        title_font_size = 36
        regular_font_size = 24
        small_font_size = 20
        
        try:
            price_font = ImageFont.truetype(font_path, price_font_size)
            title_font = ImageFont.truetype(font_path, title_font_size)
            regular_font = ImageFont.truetype(font_path, regular_font_size)
            small_font = ImageFont.truetype(font_path, small_font_size)
        except Exception:
            # Fallback to default font
            price_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
            regular_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            
        # Add gift name
        text_x = card_width // 2
        text_y = 480
        draw.text((text_x, text_y), name, fill=(0, 0, 0), font=title_font, anchor="mm")
        
        # Add prices
        # USD price
        price_x = 130
        price_y = 540
        draw.text((price_x, price_y), f"${price_usd:.0f}", fill=(0, 0, 0), font=price_font, anchor="mm")
        
        # TON price
        ton_price_x = card_width - 130
        ton_price_y = 540
        draw.text((ton_price_x, ton_price_y), f"{price_ton:.1f}".replace(".", ",").replace(",0", ""), fill=(0, 0, 0), font=price_font, anchor="mm")
        
        # Add TON logo
        ton_logo_size = (50, 50)
        ton_logo_resized = ton_logo.resize(ton_logo_size)
        ton_logo_pos = (ton_price_x - 90, ton_price_y - 25)
        card.paste(ton_logo_resized, ton_logo_pos, ton_logo_resized)
        
        # Add price labels
        draw.text((price_x, price_y + 40), "USD", fill=(100, 100, 100), font=regular_font, anchor="mm")
        draw.text((ton_price_x, ton_price_y + 40), "TON", fill=(100, 100, 100), font=regular_font, anchor="mm")
        
        # Add percent change
        percent_text = f"{'+' if change_percentage > 0 else ''}{change_percentage:.2f}%"
        percent_color = (46, 204, 113) if change_percentage >= 0 else (231, 76, 60)
        change_x = card_width // 2
        change_y = 610
        draw.text((change_x, change_y), percent_text, fill=percent_color, font=regular_font, anchor="mm")
        
        # Add chart
        chart_pos_x = 50
        chart_pos_y = 640
        card.paste(chart_image, (chart_pos_x, chart_pos_y))
        
        # Add timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        timestamp_x = card_width // 2
        timestamp_y = card_height - 30
        draw.text((timestamp_x, timestamp_y), f"Updated: {timestamp}", fill=(100, 100, 100), font=small_font, anchor="mm")
        
        # Add watermark at top center
        watermark_lines = ["@GiftsChartbot"]
        watermark_font = ImageFont.truetype(font_path, 32)
        watermark_color = (255, 255, 255, 200)  # Semi-transparent white
        line_height = watermark_font.getbbox("A")[3] + 5
        watermark_y = 30  # Start position
        
        # Draw each line centered
        for i, line in enumerate(watermark_lines):
            line_width = draw.textlength(line, font=watermark_font)
            watermark_x = card_width // 2 - line_width // 2
            line_y = watermark_y + (i * line_height)
            draw.text((watermark_x, line_y), line, fill=watermark_color, font=watermark_font)
        
        # Save the card as WebP
        if output_path.endswith('.webp'):
            output_path = output_path[:-4] + '.webp'
        card.save(output_path, 'WEBP', quality=85, method=6)
        print(f"Custom card created: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error creating custom card: {e}")
        return None 

if __name__ == "__main__":
    # Generate templates and metadata for new gifts (no price/dynamic data)
    new_gifts = [
        "Valentine Box",
        "Joyful Bundle",
        "Cupid Charm",
        "Whip Cupcake"
    ]
    for gift in new_gifts:
        print(f"Generating template and metadata for: {gift}")
        generate_template_card(gift) 

LEGACY_GIFTS_API = "https://giftcharts-api.onrender.com/gifts"
LEGACY_CHART_API = "https://giftcharts-api.onrender.com/weekChart?name=" 