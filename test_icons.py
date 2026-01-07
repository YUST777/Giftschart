
import os
import sys
import logging
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_icons')

# Mock finding assets
script_dir = "/root/01studio/giftschart"
ASSETS_DIR = os.path.join(script_dir, "assets")

# Try importing cairosvg
try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
    print("Cairosvg available")
except ImportError:
    CAIROSVG_AVAILABLE = False
    print("Cairosvg NOT available")

import io
import re

def load_icon(filename, size=(60, 60), color=None):
    """Refactored load_icon function"""
    try:
        base_name = os.path.splitext(filename)[0]
        
        # Try WebP first, then PNG, then SVG
        for ext in ['.webp', '.png', '.svg']:
            path = os.path.join(ASSETS_DIR, f"{base_name}{ext}")
            print(f"Checking {path}...")
            if not os.path.exists(path):
                continue
            
            print(f"Found {path}")
            if ext == '.svg':
                if not CAIROSVG_AVAILABLE:
                    print("Skipping SVG because cairosvg missing")
                    continue
                # Use existing SVG logic
                with open(path, 'r') as f:
                    svg_content = f.read()
                if color:
                     # Simple color replacement for test
                     pass
                png_data = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'), output_width=size[0], output_height=size[1])
                return Image.open(io.BytesIO(png_data)).convert('RGBA')

            # Load Raster Image
            img = Image.open(path).convert("RGBA")
            img = img.resize(size, Image.Resampling.LANCZOS)
            return img
            
        return None
    except Exception as e:
        logger.warning(f"Error loading icon {filename}: {e}")
        return None

def main():
    # Test Supply (Should find WebP)
    print("\n--- Testing Supply (Expected: WebP) ---")
    icon = load_icon("supply.svg")
    if icon:
        print("Success: Loaded Supply Icon")
        print(f"Format: {icon.format} Size: {icon.size}")
    else:
        print("FAIL: Supply Icon NOT loaded")

    # Test Time (Expected: SVG via CairoSVG or Fail if missing)
    print("\n--- Testing Time (Expected: SVG) ---")
    icon = load_icon("time.svg")
    if icon:
        print("Success: Loaded Time Icon")
    else:
        print("FAIL: Time Icon NOT loaded (Is cairosvg installed?)")

    # Test Premarket Cart
    print("\n--- Testing Premarket Cart (Expected: SVG) ---")
    icon = load_icon("premarket_cart.svg")
    if icon:
        print("Success: Loaded Cart Icon")
    else:
        print("FAIL: Cart Icon NOT loaded")

if __name__ == "__main__":
    main()
