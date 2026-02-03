#!/usr/bin/env python3
import os
import sys
import time
import datetime
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import schedule

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pregenerate_cards.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("pregenerate_cards")

# Add parent directory to path to import gift_card_generator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import gift_card_generator

# Path for the output cards
GIFT_CARDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "new_gift_cards")
os.makedirs(GIFT_CARDS_DIR, exist_ok=True)

# Path for tracking the last generation time
TIMESTAMP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_generation_time.txt")

def get_available_gift_names():
    """Get a list of all available gift names from main.py (includes plus premarket gifts)"""
    try:
        # Try to import the official list of gift names from main.py
        # Note: main.py already includes plus premarket gifts, so no need to add them separately
        try:
            from main import names
            logger.info(f"Using official list of {len(names)} gift names from main.py (includes plus premarket gifts)")
            return names
        except ImportError:
            logger.warning("Could not import names from main.py, falling back to directory scan")
            
            # Fallback: Get the directory where the script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Path to the downloaded images
            images_dir = os.path.join(script_dir, "downloaded_images")
            
            # Check if directory exists
            if not os.path.exists(images_dir):
                logger.error(f"Downloaded images directory not found: {images_dir}")
                os.makedirs(images_dir, exist_ok=True)
                return []
            
            # Get all PNG files
            gift_files = [f for f in os.listdir(images_dir) if f.endswith('.webp')]
            
            # Extract gift names from filenames, skipping known duplicates and special files
            gift_names = []
            skip_files = []
            
            for filename in gift_files:
                # Skip known duplicates and special files
                if filename in skip_files:
                    continue
                    
                # Remove extension and replace underscores with spaces
                gift_name = os.path.splitext(filename)[0].replace('_', ' ')
                # Handle special cases
                if gift_name == "Jack in the Box":
                    gift_name = "Jack-in-the-Box"
                elif gift_name == "Durovs Cap":
                    gift_name = "Durov's Cap"
                
                # Avoid duplicates
                if gift_name not in gift_names:
                    gift_names.append(gift_name)
            
            return gift_names
    except Exception as e:
        logger.error(f"Error getting available gift names: {e}")
        return []

def normalize_gift_filename(gift_name):
    if gift_name == "Jack-in-the-Box":
        return "Jack_in_the_Box"
    elif gift_name == "Durov's Cap":
        return "Durovs_Cap"
    else:
        return gift_name.replace(" ", "_").replace("-", "_").replace("'", "")

def generate_card(gift_name):
    """Generate a single gift card"""
    try:
        logger.info(f"Generating card for {gift_name}...")
        
        # Check if this is a plus premarket gift
        is_plus_premarket = False
        try:
            from plus_premarket_gifts import is_plus_premarket_gift
            is_plus_premarket = is_plus_premarket_gift(gift_name)
        except ImportError:
            pass
        
        normalized_filename = normalize_gift_filename(gift_name)
        
        # Plus premarket gifts use different generator and output filename
        if is_plus_premarket:
            output_path = os.path.join(GIFT_CARDS_DIR, f"{normalized_filename}.webp")
            
            # Use the dedicated plus premarket card generator
            try:
                from plus_premarket_card_generator import generate_plus_premarket_card
                import mrkt_quant_api
                
                # Fetch gift data from MRKT/Quant API (with fallback to saved JSON)
                gift_data = asyncio.run(mrkt_quant_api.fetch_gift_data(gift_name))
                
                if gift_data:
                    result = generate_plus_premarket_card(gift_name, gift_data, output_path=output_path)
                    if result:
                        logger.info(f"Successfully generated Plus Premarket card for {gift_name} at {output_path}")
                        return True
                    else:
                        logger.error(f"Failed to generate Plus Premarket card for {gift_name}")
                        return False
                else:
                    logger.error(f"No data available for Plus Premarket gift {gift_name}")
                    return False
            except Exception as e:
                logger.error(f"Error generating Plus Premarket card for {gift_name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return False
        else:
            # Regular gifts use new_card_design
            output_path = os.path.join(GIFT_CARDS_DIR, f"{normalized_filename}_card.webp")
            
            # Generate the card with force_fresh=True to bypass all caches and provide output_path
            result = asyncio.run(gift_card_generator.create_gift_card(gift_name, output_path=output_path, force_fresh=True))
            
            if result:
                logger.info(f"Successfully generated card for {gift_name} at {output_path}")
                return True
            else:
                logger.error(f"Failed to generate card for {gift_name}")
                return False
            
    except Exception as e:
        logger.error(f"Error generating card for {gift_name}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def generate_all_cards():
    """Generate all gift cards concurrently"""
    start_time = time.time()
    
    # Clear all caches before starting batch generation
    try:
        import tonnel_api
        tonnel_api.clear_all_caches()
        logger.info("🧹 CLEARED: All caches cleared before batch generation")
    except Exception as e:
        logger.warning(f"Could not clear tonnel_api caches: {e}")
    
    # Clear MRKT/Quant API caches for plus premarket gifts
    try:
        import mrkt_quant_api
        mrkt_quant_api.clear_all_caches()
        logger.info("🧹 CLEARED: MRKT/Quant API caches cleared")
    except Exception as e:
        logger.warning(f"Could not clear MRKT/Quant API caches: {e}")
    
    # Get list of gift names
    names = get_available_gift_names()
    
    if not names:
        logger.error("No gift names found")
        return
    
    logger.info(f"🔥 FORCE FRESH BATCH: Starting generation of {len(names)} cards (all gift types: +premarket, premarket, normal market) with fresh API data")
    
    # Create output directory if it doesn't exist
    os.makedirs(GIFT_CARDS_DIR, exist_ok=True)
    
    # Generate cards with a reasonable number of concurrent workers
    # Reduced for plus premarket gifts which use MRKT/Quant API (may have rate limits)
    max_workers = min(3, len(names))  # Reduced concurrent workers to avoid resource exhaustion
    successful_cards = 0
    failed_cards = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_gift = {executor.submit(generate_card, gift_name): gift_name for gift_name in names}
        
        # Process completed tasks
        for future in as_completed(future_to_gift):
            gift_name = future_to_gift[future]
            try:
                success = future.result()
                if success:
                    successful_cards += 1
                else:
                    failed_cards += 1
            except Exception as e:
                logger.error(f"Exception generating card for {gift_name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                failed_cards += 1
    
    generation_time = time.time() - start_time
    logger.info(f"Batch generation completed in {generation_time:.2f} seconds")
    logger.info(f"Successfully generated {successful_cards} cards, failed: {failed_cards}")
    
    # Update timestamp file
    try:
        with open(TIMESTAMP_FILE, 'w') as f:
            f.write(str(int(time.time())))
        logger.info(f"Updated timestamp file: {TIMESTAMP_FILE}")
    except Exception as e:
        logger.warning(f"Could not update timestamp file: {e}")
    
    return successful_cards, failed_cards

def should_regenerate():
    """Check if we should regenerate cards based on the timestamp file"""
    try:
        if not os.path.exists(TIMESTAMP_FILE):
            logger.info("No timestamp file found, will generate cards")
            return True
        
        with open(TIMESTAMP_FILE, 'r') as f:
            last_time = int(f.read().strip())
        
        current_time = int(time.time())
        
        # Check if either timestamp is in the future (system clock issue)
        current_year = datetime.datetime.fromtimestamp(current_time).year
        last_year = datetime.datetime.fromtimestamp(last_time).year
        
        # Updated for 2025 - only flag if year is clearly wrong (before 2020 or after 2030)
        if current_year < 2020 or current_year > 2030 or last_year < 2020 or last_year > 2030:
            logger.warning(f"Detected potentially incorrect system clock - current_year: {current_year}, last_year: {last_year} - forcing regeneration")
            return True
            
        elapsed_minutes = (current_time - last_time) / 60
        
        # Regenerate if more than 35 minutes have passed
        if elapsed_minutes >= 35:
            logger.info(f"Last generation was {elapsed_minutes:.1f} minutes ago, will regenerate")
            return True
        else:
            logger.info(f"Last generation was {elapsed_minutes:.1f} minutes ago, skipping")
            return False
    except Exception as e:
        logger.error(f"Error checking regeneration time: {e}")
        # If there's an error reading the timestamp, regenerate to be safe
        return True


def pregenerate_all_cards_from_templates():
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'card_templates')
    templates = [f for f in os.listdir(template_dir) if f.endswith('_template.webp')]
    for template_file in templates:
        # Extract gift name from template filename
        gift_name = template_file.replace('_template.webp', '').replace('_', ' ')
        # Handle special cases for normalization
        if gift_name == 'Jack in the Box':
            gift_name = 'Jack-in-the-Box'
        elif gift_name == 'Durovs Cap':
            gift_name = "Durov's Cap"
        print(f"Generating card for {gift_name} from template...")
        gift_card_generator.generate_specific_gift(gift_name)

def main():
    try:
        # Check if we should regenerate
        if should_regenerate():
            # Generate all cards (including plus premarket)
            successful, failed = generate_all_cards()
            
            if successful > 0:
                logger.info(f"All done! Generated {successful} cards (including +premarket, premarket, and normal market gifts)")
            else:
                logger.warning("No cards were successfully generated")
        else:
            logger.info("Skipping generation as cards are still fresh")
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    schedule.every(35).minutes.do(main)
    print("Starting scheduled card generation every 35 minutes...")
    main()  # Run once at startup
    while True:
        schedule.run_pending()
        time.sleep(10) 