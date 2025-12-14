#!/usr/bin/env python3
"""
Generate All Sticker Price Cards

This script generates price cards for all stickers with prices using the updated design
that includes hardcoded sale prices and supply information.
"""

import os
import json
import time
import logging
import argparse
import sys
from datetime import datetime
from sticker_price_card_generator import generate_price_card, load_price_data
import stickers_tools_api as sticker_api
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("generate_all_sticker_price_cards")

# Get script directory for cross-platform compatibility
script_dir = os.path.dirname(os.path.abspath(__file__))

# Constants
PRICE_DATA_FILE = os.path.join(script_dir, "sticker_price_results.json")
OUTPUT_DIR = os.path.join(script_dir, "Sticker_Price_Cards")

# Windows-safe print function
def safe_print(text):
    """Print text safely on Windows by handling Unicode issues"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Replace problematic characters with safe alternatives
        safe_text = text.replace('📂', '[FILE]').replace('📅', '[TIME]').replace('❌', '[ERROR]').replace('✅', '[OK]').replace('🟢', '[FRESH]').replace('🔴', '[STALE]').replace('⚪', '[UNKNOWN]').replace('🎯', '[TARGET]').replace('📊', '[STATS]').replace('⏱️', '[TIME]').replace('⚡', '[FAST]').replace('⚠️', '[WARN]')
        try:
            print(safe_text)
        except UnicodeEncodeError:
            # If still fails, use a more aggressive replacement
            safe_text = safe_text.encode('ascii', 'ignore').decode('ascii')
            print(safe_text)

def normalize_name(name):
    name = name.strip().lower()
    name = re.sub(r'[^a-z0-9]', '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip('_')

def check_data_freshness():
    """Check if the price data is fresh or cached"""
    try:
        if not os.path.exists(PRICE_DATA_FILE):
            return "NO DATA", 0
        
        with open(PRICE_DATA_FILE, 'r') as f:
            data = json.load(f)
        
        timestamp = data.get("timestamp", 0)
        current_time = time.time()
        age_seconds = current_time - timestamp
        age_minutes = age_seconds / 60
        
        if age_minutes < 32:
            return "FRESH", age_minutes, data.get("human_timestamp", "unknown")
        else:
            return "STALE", age_minutes, data.get("human_timestamp", "unknown")
    except Exception as e:
        logger.error(f"Error checking data freshness: {e}")
        return "UNKNOWN", 0, "unknown"

def generate_all_price_cards(price_data, output_dir):
    """Generate price cards for all stickers with prices"""
    if not price_data or 'stickers_with_prices' not in price_data:
        logger.error("Invalid price data")
        safe_print("❌ Invalid price data format")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Import cache counters from sticker_price_card_generator
    from sticker_price_card_generator import cached_usage, live_api_usage
    
    # Reset counters
    import sticker_price_card_generator
    sticker_price_card_generator.cached_usage = 0
    sticker_price_card_generator.live_api_usage = 0
    
    # Track results
    successful = 0
    failed = 0
    
    # Get data freshness
    status, age, timestamp = check_data_freshness()
    freshness_indicator = "🟢" if status == "FRESH" else "🔴" if status == "STALE" else "⚪"
    
    # Get stickers
    stickers = price_data['stickers_with_prices']
    total_stickers = len(stickers)
    
    safe_print(f"\n{freshness_indicator} GENERATING PRICE CARDS: Using {status} data ({age:.2f} minutes old)")
    safe_print(f"📅 Data timestamp: {timestamp}")
    safe_print(f"🎯 Generating {total_stickers} price cards...")
    
    # Track start time
    start_time = time.time()
    
    # Generate cards for each sticker with price
    for i, item in enumerate(stickers):
        collection = normalize_name(item['collection'])
        sticker = normalize_name(item['sticker'])
        price = item['price']
        
        # Calculate progress percentage
        progress = (i + 1) / total_stickers * 100
        
        logger.info(f"Generating price card for {collection} - {sticker}: {price} TON")
        
        card_start_time = time.time()
        result = generate_price_card(collection, sticker, price, output_dir)
        card_time = time.time() - card_start_time
        
        if result:
            successful += 1
            safe_print(f"  ✅ {i+1}/{total_stickers} {collection} - {sticker}: {price} TON ({card_time:.2f}s)")
        else:
            failed += 1
            safe_print(f"  ❌ {i+1}/{total_stickers} {collection} - {sticker}: Failed ({card_time:.2f}s)")
        
        # Create a progress bar (every 5%)
        if (i + 1) % max(1, int(total_stickers / 20)) == 0 or i == total_stickers - 1:
            bar_length = 30
            filled_length = int(bar_length * progress / 100)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            
            # Calculate ETA
            elapsed_time = time.time() - start_time
            items_per_second = (i + 1) / elapsed_time if elapsed_time > 0 else 0
            remaining_items = total_stickers - (i + 1)
            eta_seconds = remaining_items / items_per_second if items_per_second > 0 else 0
            
            safe_print(f"  [{bar}] {progress:.1f}% Complete - ETA: {int(eta_seconds//60)}m {int(eta_seconds%60)}s")
    
    # Get final cache counts
    from sticker_price_card_generator import cached_usage, live_api_usage
    
    # Calculate total execution time
    execution_time = time.time() - start_time
    
    logger.info(f"Price card generation complete: {successful} successful ({cached_usage} from cache, {live_api_usage} from live API), {failed} failed in {execution_time:.2f} seconds")
    safe_print(f"\n✅ GENERATION COMPLETE: {successful}/{total_stickers} cards generated successfully")
    safe_print(f"📊 Data sources: {cached_usage} from cache, {live_api_usage} from live API")
    safe_print(f"⏱️ Total execution time: {execution_time:.2f} seconds")
    safe_print(f"⚡ Average time per card: {(execution_time/total_stickers):.2f} seconds")
    
    if failed > 0:
        safe_print(f"⚠️ {failed} cards failed to generate")
    
    return successful, failed

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate all sticker price cards")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory for generated cards")
    args = parser.parse_args()
    
    os.system('clear')  # Clear the terminal for clean logs
    # Fetch all collections and stickers from the live API
    stats = sticker_api.get_sticker_stats(force_refresh=True)
    total = 0
    for collection in stats["collections"].values():
        collection_name = normalize_name(collection["name"])
        for sticker in collection["stickers"]:
            sticker_name = normalize_name(sticker["name"])
            price_info = sticker_api.get_sticker_price(collection_name, sticker_name, force_refresh=True)
            if price_info and price_info["floor_price_ton"] > 0:
                price = price_info["floor_price_ton"]
                generate_price_card(collection_name, sticker_name, price, args.output_dir)
                total += 1
    print(f"✅ Generated {total} price cards from live API data.")

if __name__ == "__main__":
    main() 