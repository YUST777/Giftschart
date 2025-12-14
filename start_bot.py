#!/usr/bin/env python3
"""
Telegram Gift & Sticker Bot Startup Script

This script handles:
- Dependency verification
- Database initialization
- Rate limiter setup
- Premium system initialization
- Bot startup with proper error handling
"""

import os
import sys
import subprocess
import importlib
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        return False
    logger.info(f"Python version: {sys.version}")
    return True

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        'telegram',
        'PIL',
        'matplotlib',
        'numpy',
        'requests',
        'httpx',
        'psycopg2',
        'yaml',
        'schedule'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            logger.info(f"✓ {package} is available")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"✗ {package} is missing")
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.info("Installing missing packages...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            logger.info("Dependencies installed successfully")
        except subprocess.CalledProcessError:
            logger.error("Failed to install dependencies")
            return False
    
    return True

def initialize_databases():
    """Initialize all required databases."""
    try:
        # Initialize rate limiter database
        from rate_limiter import init_db
        init_db()
        logger.info("✓ Rate limiter database initialized")
        
        # Initialize premium system database
        from premium_system import PremiumSystem
        premium_system = PremiumSystem()
        logger.info("✓ Premium system database initialized")
        
        return True
    except Exception as e:
        logger.error(f"Failed to initialize databases: {e}")
        return False

def check_file_structure():
    """Check if all required files and directories exist."""
    required_files = [
        "telegram_bot.py",
        "bot_config.py",
        "rate_limiter.py",
        "premium_system.py"
    ]
    
    required_dirs = [
        "new_gift_cards",
        "card_templates",
        "downloaded_images",
        "card_metadata"
    ]
    
    missing_items = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_items.append(f"File: {file}")
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            missing_items.append(f"Directory: {directory}")
    
    if missing_items:
        logger.error(f"Missing items: {', '.join(missing_items)}")
        return False
    
    logger.info("✓ All required files and directories found")
    return True

def cleanup_cache():
    """Clean up Python cache files."""
    try:
        import shutil
        cache_dirs = []
        
        # Find all __pycache__ directories
        for root, dirs, files in os.walk('.'):
            for dir in dirs:
                if dir == '__pycache__':
                    cache_dirs.append(os.path.join(root, dir))
        
        # Remove cache directories
        for cache_dir in cache_dirs:
            shutil.rmtree(cache_dir)
            logger.info(f"Cleaned cache: {cache_dir}")
        
        logger.info("✓ Cache cleanup completed")
        return True
    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")
        return False

def start_backup_process():
    """Start the hourly DB backup script in the background."""
    backup_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sqlite_data", "backup_db_hourly.py")
    subprocess.Popen([sys.executable, backup_script])

def start_bot():
    """Start the Telegram bot."""
    try:
        logger.info("Starting Telegram bot...")
        
        # Import and run the main bot
        from telegram_bot import main
        main()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot startup failed: {e}")
        return False
    
    return True

def main():
    """Main startup function."""
    logger.info("=" * 50)
    logger.info("Telegram Gift & Sticker Bot Startup")
    logger.info("=" * 50)
    
    # Start the backup process
    start_backup_process()
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Step 1: Check Python version
    logger.info("Step 1: Checking Python version...")
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Check dependencies
    logger.info("Step 2: Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    # Step 3: Check file structure
    logger.info("Step 3: Checking file structure...")
    if not check_file_structure():
        sys.exit(1)
    
    # Step 4: Clean up cache
    logger.info("Step 4: Cleaning up cache...")
    cleanup_cache()
    
    # Step 5: Initialize databases
    logger.info("Step 5: Initializing databases...")
    if not initialize_databases():
        sys.exit(1)
    
    # Step 6: Start the bot
    logger.info("Step 6: Starting bot...")
    if not start_bot():
        sys.exit(1)

if __name__ == "__main__":
    main() 