#!/usr/bin/env python3
"""
Scheduled Sticker Update

This script runs the fetch_sticker_prices.py script periodically (every 30 minutes)
to keep the database updated with real-time price data from stickers.tools API
and regenerate all price cards.
"""

import os
import sys
import time
import json
import logging
import subprocess
import schedule
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('scheduled_sticker_update')

# Get script directory for cross-platform compatibility
script_dir = os.path.dirname(os.path.abspath(__file__))

# Constants - use os.path.join for cross-platform compatibility
PRICE_DATA_FILE = os.path.join(script_dir, "sticker_price_results.json")

# Path to the scripts
FETCH_SCRIPT = "fetch_sticker_prices.py"
GENERATE_CARDS_SCRIPT = "generate_all_sticker_price_cards.py"

# Function to check data freshness
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
        
        if age_minutes < 60:
            return "FRESH", age_minutes
        else:
            return "STALE", age_minutes
    except Exception as e:
        logger.error(f"Error checking data freshness: {e}")
        return "UNKNOWN", 0

# Function to run the fetch script
def run_fetch_script():
    """Run the fetch_sticker_prices.py script"""
    try:
        start_time = time.time()
        logger.info(f"Running {FETCH_SCRIPT} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run the script as a subprocess
        result = subprocess.run([sys.executable, FETCH_SCRIPT], 
                               capture_output=True, 
                               text=True)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Log the output
        if result.stdout:
            logger.info(f"Output from {FETCH_SCRIPT}:\n{result.stdout}")
        if result.stderr:
            logger.error(f"Error output from {FETCH_SCRIPT}:\n{result.stderr}")
            
        # Check the return code
        if result.returncode == 0:
            logger.info(f"Successfully ran {FETCH_SCRIPT} in {execution_time:.2f} seconds")
            print(f"✅ Stickers.tools API data fetched successfully in {execution_time:.2f} seconds")
        else:
            logger.error(f"Failed to run {FETCH_SCRIPT}, return code: {result.returncode}")
            print(f"❌ Failed to fetch stickers.tools API data, error code: {result.returncode}")
            
        return result.returncode == 0, execution_time
    except Exception as e:
        logger.error(f"Error running {FETCH_SCRIPT}: {e}")
        print(f"❌ Error fetching stickers.tools API data: {e}")
        return False, 0

# Function to generate price cards
def generate_price_cards():
    """Generate price cards for all stickers"""
    try:
        start_time = time.time()
        logger.info(f"Running {GENERATE_CARDS_SCRIPT} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run the script as a subprocess
        result = subprocess.run([sys.executable, GENERATE_CARDS_SCRIPT], 
                               capture_output=True, 
                               text=True)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Log the output
        if result.stdout:
            logger.info(f"Output from {GENERATE_CARDS_SCRIPT}:\n{result.stdout}")
        if result.stderr:
            logger.error(f"Error output from {GENERATE_CARDS_SCRIPT}:\n{result.stderr}")
            
        # Check the return code
        if result.returncode == 0:
            logger.info(f"Successfully generated price cards in {execution_time:.2f} seconds")
            print(f"✅ Price cards generated successfully in {execution_time:.2f} seconds")
        else:
            logger.error(f"Failed to generate price cards, return code: {result.returncode}")
            print(f"❌ Failed to generate price cards, error code: {result.returncode}")
            
        return result.returncode == 0, execution_time
    except Exception as e:
        logger.error(f"Error generating price cards: {e}")
        print(f"❌ Error generating price cards: {e}")
        return False, 0

# Function to run the complete update process
def run_update_process():
    """Run the complete update process: fetch prices and generate cards"""
    total_start_time = time.time()
    
    # Check data freshness before update
    status, age = check_data_freshness()
    freshness_indicator = "🟢" if status == "FRESH" else "🔴" if status == "STALE" else "⚪"
    logger.info(f"Current data status: {status}, age: {age:.2f} minutes")
    
    logger.info("Starting update process")
    print(f"\n{freshness_indicator} STARTING UPDATE PROCESS: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Current data status: {status} ({age:.2f} minutes old)")
    
    # Step 1: Fetch prices from stickers.tools API
    fetch_success, fetch_time = run_fetch_script()
    
    # Step 2: Generate cards if fetch was successful
    if fetch_success:
        logger.info("Fetch successful, generating price cards")
        gen_success, gen_time = generate_price_cards()
    else:
        logger.error("Fetch failed, skipping card generation")
        print("❌ Fetch failed, skipping card generation")
        gen_time = 0
    
    # Calculate total execution time
    total_time = time.time() - total_start_time
    
    # Check data freshness after update
    status, age = check_data_freshness()
    freshness_indicator = "🟢" if status == "FRESH" else "🔴" if status == "STALE" else "⚪"
    
    logger.info(f"Update process complete in {total_time:.2f} seconds")
    print(f"✅ UPDATE PROCESS COMPLETE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️ Total execution time: {total_time:.2f} seconds (Fetch: {fetch_time:.2f}s, Generate: {gen_time:.2f}s)")
    print(f"{freshness_indicator} Data status: {status} ({age:.2f} minutes old)")

# Function to display time until next update
def display_time_remaining():
    """Display time remaining until next update"""
    next_run = schedule.next_run()
    if next_run:
        now = datetime.now()
        time_diff = next_run - now
        minutes_remaining = time_diff.total_seconds() / 60
        seconds_remaining = time_diff.total_seconds() % 60
        
        # Calculate percentage of time elapsed
        percent_elapsed = ((60 * 60) - time_diff.total_seconds()) / (60 * 60) * 100
        
        # Create a progress bar
        bar_length = 20
        filled_length = int(bar_length * percent_elapsed / 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        print(f"\n⏱️  Next update in {int(minutes_remaining)} minutes {int(seconds_remaining)} seconds ({next_run.strftime('%H:%M:%S')})")
        print(f"[{bar}] {percent_elapsed:.1f}% elapsed")
        
        # Check data freshness
        status, age = check_data_freshness()
        freshness_indicator = "🟢" if status == "FRESH" else "🔴" if status == "STALE" else "⚪"
        print(f"{freshness_indicator} Data status: {status} ({age:.2f} minutes old)")
        
        logger.info(f"Next update in {int(minutes_remaining)} minutes {int(seconds_remaining)} seconds ({next_run.strftime('%H:%M:%S')})")

# Main function
def main():
    """Main function"""
    try:
        logger.info("Starting scheduled sticker update service")
        print(f"🚀 STARTING PRICE UPDATE SERVICE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 Updates will run every 30 minutes using stickers.tools API")
        
        # Run once at startup
        run_update_process()
        
        # Schedule to run every 30 minutes
        schedule.every(30).minutes.do(run_update_process)
        
        # Schedule to display time remaining every minute
        schedule.every(1).minutes.do(display_time_remaining)
        
        logger.info("Scheduled tasks set up. Running every 30 minutes.")
        
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Scheduled sticker update stopped by user")
        print("\n⛔ Service stopped by user")
    except Exception as e:
        logger.error(f"Error in scheduled sticker update: {e}")
        print(f"\n❌ Service error: {e}")

if __name__ == "__main__":
    main() 