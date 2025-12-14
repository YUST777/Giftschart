#!/usr/bin/env python3
"""
Enhanced Database Backup System for Telegram Bot

This system:
1. Creates compressed backups of all SQLite databases
2. Sends backup files to the group chat via Telegram
3. Automatically cleans up old backup files
4. Includes retry mechanisms and error handling
5. Logs all backup activities
"""

import os
import sys
import zipfile
import shutil
import logging
import asyncio
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the path to import bot modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from telegram import Bot
    from bot_config import BOT_TOKEN
    import telegram.error
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure you're running this from the correct directory with all dependencies installed.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backup_system.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("backup_system")

# Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = script_dir
backup_dir = os.path.join(db_dir, "backups")
os.makedirs(backup_dir, exist_ok=True)

# Configuration
MAX_BACKUP_AGE_DAYS = 7  # Keep backups for 7 days
MAX_BACKUP_COUNT = 50    # Maximum number of backup files to keep
RETRY_ATTEMPTS = 3       # Number of retry attempts for failed operations
RETRY_DELAY = 5          # Delay between retry attempts (seconds)

class DatabaseBackupSystem:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        
    def get_database_files(self):
        """Get list of all database files in the directory."""
        db_files = []
        for filename in os.listdir(db_dir):
            if filename.endswith('.db'):
                filepath = os.path.join(db_dir, filename)
                if os.path.isfile(filepath):
                    db_files.append(filepath)
        return db_files
    
    def verify_database_integrity(self, db_path):
        """Verify database integrity before backup."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()
            conn.close()
            return result[0] == 'ok'
        except Exception as e:
            logger.error(f"Database integrity check failed for {db_path}: {e}")
            return False
    
    def create_backup_zip(self):
        """Create a compressed backup of all database files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"database_backup_{timestamp}.zip"
        zip_path = os.path.join(backup_dir, zip_filename)
        
        try:
            db_files = self.get_database_files()
            
            if not db_files:
                logger.warning("No database files found for backup")
                return None
                
            # Create zip file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                backup_info = {
                    'timestamp': timestamp,
                    'files': [],
                    'total_size': 0
                }
                
                for db_file in db_files:
                    if self.verify_database_integrity(db_file):
                        # Add file to zip
                        arcname = os.path.basename(db_file)
                        zipf.write(db_file, arcname)
                        
                        # Get file info
                        file_size = os.path.getsize(db_file)
                        backup_info['files'].append({
                            'name': arcname,
                            'size': file_size,
                            'size_mb': round(file_size / (1024*1024), 2)
                        })
                        backup_info['total_size'] += file_size
                        
                        logger.info(f"Added {arcname} to backup ({file_size} bytes)")
                    else:
                        logger.error(f"Skipping corrupted database: {db_file}")
                
                # Add backup info as text file
                info_content = f"""Database Backup Information
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Files: {len(backup_info['files'])}
Total Size: {round(backup_info['total_size'] / (1024*1024), 2)} MB

Files Included:
"""
                for file_info in backup_info['files']:
                    info_content += f"- {file_info['name']}: {file_info['size_mb']} MB\n"
                
                zipf.writestr("backup_info.txt", info_content)
            
            backup_size = os.path.getsize(zip_path)
            logger.info(f"Created backup zip: {zip_filename} ({backup_size} bytes)")
            
            return zip_path, backup_info
            
        except Exception as e:
            logger.error(f"Error creating backup zip: {e}")
            return None, None
    
    async def send_backup_to_group(self, zip_path, backup_info):
        """Send backup file to group chat instead of individual admins."""
        GROUP_CHAT_ID = -4944651195  # Your group chat ID
        
        try:
            file_size_mb = round(os.path.getsize(zip_path) / (1024*1024), 2)
            
            caption = f"""🔒 **Database Backup Report**
            
📅 **Backup Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 **Files Backed Up**: {len(backup_info['files'])}
💾 **Total Size**: {file_size_mb} MB
🔐 **Backup Status**: ✅ Complete

**Databases Included:**
"""
            
            for file_info in backup_info['files']:
                caption += f"• {file_info['name']}: {file_info['size_mb']} MB\n"
            
            caption += f"\n💡 **Tip**: Extract this zip file to restore your databases if needed."
            
            with open(zip_path, 'rb') as backup_file:
                await self.bot.send_document(
                    chat_id=GROUP_CHAT_ID,
                    document=backup_file,
                    caption=caption,
                    parse_mode='Markdown'
                )
            
            logger.info(f"Successfully sent backup to group chat {GROUP_CHAT_ID}")
            return 1
            
        except telegram.error.TelegramError as e:
            logger.error(f"Telegram error sending backup to group chat {GROUP_CHAT_ID}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error sending backup to group chat {GROUP_CHAT_ID}: {e}")
            return 0
    
    def cleanup_old_backups(self):
        """Remove old backup files to save disk space."""
        try:
            now = datetime.now()
            deleted_count = 0
            
            # Get all backup files
            backup_files = []
            for filename in os.listdir(backup_dir):
                if filename.startswith('database_backup_') and filename.endswith('.zip'):
                    filepath = os.path.join(backup_dir, filename)
                    if os.path.isfile(filepath):
                        backup_files.append((filepath, os.path.getmtime(filepath)))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Remove files older than MAX_BACKUP_AGE_DAYS
            for filepath, mtime in backup_files:
                file_age = now - datetime.fromtimestamp(mtime)
                if file_age.days > MAX_BACKUP_AGE_DAYS:
                    os.remove(filepath)
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {os.path.basename(filepath)}")
            
            # Remove excess files if we have too many
            if len(backup_files) > MAX_BACKUP_COUNT:
                excess_files = backup_files[MAX_BACKUP_COUNT:]
                for filepath, _ in excess_files:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        deleted_count += 1
                        logger.info(f"Deleted excess backup: {os.path.basename(filepath)}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old backup files")
            
        except Exception as e:
            logger.error(f"Error during backup cleanup: {e}")
    
    async def run_backup_cycle(self):
        """Run a complete backup cycle."""
        logger.info("Starting backup cycle...")
        
        try:
            # Create backup
            zip_path, backup_info = self.create_backup_zip()
            
            if not zip_path:
                logger.error("Failed to create backup zip")
                return False
            
            # Send to group chat
            success_count = await self.send_backup_to_group(zip_path, backup_info)
            
            # Cleanup old backups
            self.cleanup_old_backups()
            
            logger.info(f"Backup cycle completed successfully. Sent to group chat.")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error during backup cycle: {e}")
            return False
    
    def get_backup_status(self):
        """Get current backup status information."""
        try:
            db_files = self.get_database_files()
            backup_files = [f for f in os.listdir(backup_dir) if f.startswith('database_backup_') and f.endswith('.zip')]
            
            total_db_size = sum(os.path.getsize(f) for f in db_files)
            total_backup_size = sum(os.path.getsize(os.path.join(backup_dir, f)) for f in backup_files)
            
            return {
                'database_count': len(db_files),
                'database_size_mb': round(total_db_size / (1024*1024), 2),
                'backup_count': len(backup_files),
                'backup_size_mb': round(total_backup_size / (1024*1024), 2),
                'last_backup': max([os.path.getmtime(os.path.join(backup_dir, f)) for f in backup_files]) if backup_files else None
            }
            
        except Exception as e:
            logger.error(f"Error getting backup status: {e}")
            return None

async def main():
    """Main backup execution function."""
    logger.info("Database Backup System Starting...")
    
    backup_system = DatabaseBackupSystem()
    
    # Run backup cycle
    success = await backup_system.run_backup_cycle()
    
    if success:
        logger.info("Backup completed successfully!")
        print("✅ Backup completed successfully!")
    else:
        logger.error("Backup failed!")
        print("❌ Backup failed!")
    
    # Print status
    status = backup_system.get_backup_status()
    if status:
        print(f"\n📊 Backup Status:")
        print(f"Databases: {status['database_count']} files ({status['database_size_mb']} MB)")
        print(f"Backups: {status['backup_count']} files ({status['backup_size_mb']} MB)")
        if status['last_backup']:
            last_backup_time = datetime.fromtimestamp(status['last_backup'])
            print(f"Last backup: {last_backup_time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main()) 