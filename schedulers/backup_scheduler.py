#!/usr/bin/env python3
"""
Database Backup Scheduler

This script runs the enhanced backup system every hour and includes:
- Automatic hourly backups
- Message ownership cleanup
- Graceful shutdown handling
- Comprehensive logging
- Error recovery mechanisms
- System health monitoring
"""

import os
import sys
import time
import signal
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from pathlib import Path

# Add the sqlite_data directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sqlite_data'))

try:
    from enhanced_backup_system import DatabaseBackupSystem
except ImportError as e:
    print(f"Error importing backup system: {e}")
    sys.exit(1)

# Import rate_limiter for message ownership cleanup
try:
    from rate_limiter import cleanup_old_message_ownership, get_message_ownership_stats
except ImportError as e:
    print(f"Warning: Could not import rate_limiter for message cleanup: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backup_scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("backup_scheduler")

# Global variables
running = True
backup_system = None
last_backup_time = None
backup_interval = 3600  # 1 hour in seconds

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    running = False

def calculate_next_backup_time():
    """Calculate the next backup time on the hour."""
    now = datetime.now()
    next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return next_hour

async def perform_backup():
    """Perform a backup and handle any errors."""
    global last_backup_time, backup_system
    
    try:
        logger.info("Starting scheduled backup...")
        
        if not backup_system:
            backup_system = DatabaseBackupSystem()
        
        success = await backup_system.run_backup_cycle()
        
        if success:
            last_backup_time = datetime.now()
            logger.info("Scheduled backup completed successfully")
            
            # Perform message ownership cleanup
            try:
                if 'cleanup_old_message_ownership' in globals():
                    cleanup_old_message_ownership(max_age_hours=24)
                    
                    # Log cleanup statistics
                    if 'get_message_ownership_stats' in globals():
                        stats = get_message_ownership_stats()
                        logger.info(f"Message ownership cleanup completed. "
                                  f"Total messages: {stats['total_messages']}, "
                                  f"Total linked messages: {stats['total_linked_messages']}")
                else:
                    logger.warning("Message ownership cleanup not available")
            except Exception as e:
                logger.error(f"Error during message ownership cleanup: {e}")
            
            return True
        else:
            logger.error("Scheduled backup failed")
            return False
            
    except Exception as e:
        logger.error(f"Error during scheduled backup: {e}")
        return False

def get_system_status():
    """Get current system status information."""
    try:
        if backup_system:
            status = backup_system.get_backup_status()
            if status:
                return {
                    'last_backup': last_backup_time.strftime('%Y-%m-%d %H:%M:%S') if last_backup_time else 'Never',
                    'database_count': status['database_count'],
                    'database_size_mb': status['database_size_mb'],
                    'backup_count': status['backup_count'],
                    'backup_size_mb': status['backup_size_mb'],
                    'next_backup': calculate_next_backup_time().strftime('%Y-%m-%d %H:%M:%S')
                }
        return None
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return None

async def backup_scheduler():
    """Main backup scheduler loop."""
    global running, last_backup_time
    
    logger.info("Database Backup Scheduler started")
    
    # Perform initial backup
    await perform_backup()
    
    while running:
        try:
            now = datetime.now()
            next_backup = calculate_next_backup_time()
            
            # If it's past the next backup time, perform backup
            if now >= next_backup:
                await perform_backup()
                
                # Wait until next hour
                next_backup = calculate_next_backup_time()
            
            # Sleep for a short time to avoid busy waiting
            sleep_time = min(60, (next_backup - now).total_seconds())
            
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            
        except Exception as e:
            logger.error(f"Error in backup scheduler loop: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    logger.info("Backup scheduler stopped")

def status_monitor():
    """Monitor and log system status periodically."""
    while running:
        try:
            status = get_system_status()
            if status:
                logger.info(f"System Status - Last backup: {status['last_backup']}, "
                           f"DBs: {status['database_count']} ({status['database_size_mb']} MB), "
                           f"Backups: {status['backup_count']} ({status['backup_size_mb']} MB)")
        except Exception as e:
            logger.error(f"Error in status monitor: {e}")
        
        # Log status every 30 minutes
        time.sleep(1800)

async def main():
    """Main function to run the backup scheduler."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start status monitor in a separate thread
    monitor_thread = threading.Thread(target=status_monitor, daemon=True)
    monitor_thread.start()
    
    # Start backup scheduler
    await backup_scheduler()
    
    logger.info("Database Backup Scheduler shutting down...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Backup scheduler interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in backup scheduler: {e}")
        sys.exit(1) 