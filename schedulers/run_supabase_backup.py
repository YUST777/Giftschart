#!/usr/bin/env python3
"""
Automated Supabase Backup Scheduler

Runs the Supabase backup sync every 6 hours automatically.
This keeps your cloud backup fresh without manual intervention.
"""

import sys
import os
import time
import logging
from datetime import datetime, timedelta
import schedule

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schedulers.supabase_backup_sync import SupabaseBackupSync

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global syncer instance
syncer = SupabaseBackupSync()

def run_backup_job():
    """Job function that runs the backup sync."""
    try:
        logger.info("🔔 Scheduled backup job triggered")
        result = syncer.run_full_sync()
        
        if result['success']:
            logger.info("✅ Scheduled backup completed successfully")
        else:
            logger.error("❌ Scheduled backup failed")
            
    except Exception as e:
        logger.error(f"❌ Backup job error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run the backup scheduler."""
    logger.info("=" * 60)
    logger.info("🚀 Supabase Backup Scheduler Started")
    logger.info("=" * 60)
    logger.info("⏰ Backup Frequency: Every 6 hours")
    logger.info("📍 Next backup will run in 6 hours")
    logger.info("💡 Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    # Schedule backup every 6 hours
    schedule.every(6).hours.do(run_backup_job)
    
    # Run initial backup immediately
    logger.info("🔄 Running initial backup now...")
    run_backup_job()
    
    # Calculate next run time
    next_run = datetime.now() + timedelta(hours=6)
    logger.info(f"⏰ Next backup scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  Scheduler stopped by user")
        logger.info(f"📊 Total backups completed: {syncer.sync_count}")
        if syncer.last_sync_time:
            logger.info(f"🕐 Last backup: {syncer.last_sync_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.error(f"❌ Scheduler error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
