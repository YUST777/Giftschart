#!/usr/bin/env python3
"""
Combined Sticker Price Fetch & Card Generation Scheduler

This script, every 32 minutes:
  1. Fetches sticker prices from the API and saves to JSON
  2. Generates all price cards from the new data
  3. Logs and prints status

It is Windows-safe and does not modify the original scripts.
"""
import os
import sys
import time
import logging
import json
import subprocess
from datetime import datetime
from sticker_price_card_generator import generate_all_price_cards

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sticker_price_update_and_cardgen.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("sticker_price_update_and_cardgen")

script_dir = os.path.dirname(os.path.abspath(__file__))
PRICE_DATA_FILE = os.path.join(script_dir, "sticker_price_results.json")
OUTPUT_DIR = os.path.join(script_dir, "Sticker_Price_Cards")
INTERVAL_SECONDS = 32 * 60

# Windows-safe print function
def safe_print(text):
    """Print text safely on Windows by handling Unicode issues"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Replace problematic characters with safe alternatives
        safe_text = text.replace('🔑', '[AUTH]').replace('📂', '[FILE]').replace('⚠️', '[WARN]').replace('❌', '[ERROR]').replace('🔄', '[UPDATE]').replace('✅', '[OK]').replace('ℹ️', '[INFO]').replace('📊', '[STATS]').replace('⏱️', '[TIME]').replace('⚡', '[FAST]').replace('💾', '[SAVE]')
        try:
            print(safe_text)
        except UnicodeEncodeError:
            # If still fails, use a more aggressive replacement
            safe_text = safe_text.encode('ascii', 'ignore').decode('ascii')
            print(safe_text)

def fetch_and_save_prices():
    """Fetch sticker prices using the existing optimized script"""
    try:
        safe_print(f"[TIME] Fetching sticker prices at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run the existing fetch script
        result = subprocess.run([sys.executable, "fetch_sticker_prices.py"], 
                               capture_output=True, 
                               text=True,
                               timeout=300)  # 5 minute timeout
        
        if result.returncode == 0:
            safe_print(f"[OK] Price fetching completed successfully")
            return True
        else:
            safe_print(f"[ERROR] Price fetching failed with code {result.returncode}")
            if result.stderr:
                safe_print(f"[ERROR] Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        safe_print(f"[ERROR] Price fetching timed out after 5 minutes")
        return False
    except Exception as e:
        safe_print(f"[ERROR] Error during price fetching: {e}")
        return False

def main_loop():
    safe_print(f"[START] Combined Sticker Price Update & Card Generation Service")
    safe_print(f"[INFO] Will run every {INTERVAL_SECONDS//60} minutes")
    safe_print(f"[INFO] Output directory: {OUTPUT_DIR}")
    
    while True:
        start_time = time.time()
        safe_print("\n" + "="*50)
        safe_print(f"[CYCLE] Starting cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Fetch prices
        fetch_success = fetch_and_save_prices()
        
        # Step 2: Generate cards if fetch succeeded
        if fetch_success:
            try:
                safe_print(f"[INFO] Loading price data for card generation...")
                with open(PRICE_DATA_FILE, 'r') as f:
                    price_data = json.load(f)
                
                sticker_count = len(price_data.get('stickers_with_prices', []))
                safe_print(f"[INFO] Generating cards for {sticker_count} stickers...")
                
                result = generate_all_price_cards(price_data, OUTPUT_DIR)
                safe_print(f"[OK] Card generation completed successfully")
                
            except Exception as e:
                logger.error(f"Error generating price cards: {e}")
                safe_print(f"[ERROR] Failed to generate price cards: {e}")
        else:
            safe_print("[WARN] Skipping card generation due to fetch failure.")
        
        # Calculate timing
        elapsed = time.time() - start_time
        sleep_time = max(0, INTERVAL_SECONDS - elapsed)
        
        safe_print(f"[TIME] Cycle completed in {elapsed:.1f} seconds")
        safe_print(f"[WAIT] Sleeping {int(sleep_time//60)}m {int(sleep_time%60)}s until next cycle...")
        
        time.sleep(sleep_time)

if __name__ == "__main__":
    main_loop() 