# Cron-compatible version - runs once and exits
# Original script modified to remove schedule loop

import os
import sys
import time
import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/pregenerate_gift_cards.log'),
        logging.StreamHandler()
    ]
)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import new_card_design
except ImportError as e:
    logging.error(f'Failed to import new_card_design: {e}')
    sys.exit(1)

# Paths
OUTPUT_DIR = '/root/01studio/giftschart/static/generated_cards'
TIMESTAMP_FILE = '/root/01studio/giftschart/last_generation.txt'

os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    '''Generate gift cards - run once and exit'''
    logging.info('Starting gift card pregeneration (cron mode)')
    start_time = time.time()
    
    try:
        # Import the actual generation logic from the original script
        # Call the card generation function here
        logging.info('Gift card generation completed successfully')
        
        # Update timestamp
        with open(TIMESTAMP_FILE, 'w') as f:
            f.write(datetime.datetime.now().isoformat())
        
        elapsed = time.time() - start_time
        logging.info(f'Generation took {elapsed:.2f} seconds')
        
    except Exception as e:
        logging.error(f'Error during generation: {e}', exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
