# Cron-compatible version - just run the existing script's main function
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the update process from the original script
from scheduled_sticker_update import run_update_process

if __name__ == '__main__':
    # Just run once and exit
    run_update_process()
