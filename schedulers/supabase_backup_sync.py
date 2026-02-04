#!/usr/bin/env python3
"""
Supabase Backup Sync for GiftsChart Bot

This script syncs SQLite data to Supabase as a cloud backup.
Runs periodically to ensure data is backed up to the cloud.

Architecture:
- Primary: SQLite (fast, local)
- Backup: Supabase (cloud, disaster recovery)
"""

import sys
import os
import sqlite3
import time
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.paths import PREMIUM_DB_FILE, USER_REQUESTS_DB_FILE
from core.supabase_client import (
    SUPABASE_ENABLED,
    PSYCOPG2_AVAILABLE,
    get_connection,
    release_connection,
    init_tables
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SupabaseBackupSync:
    """Sync SQLite data to Supabase as cloud backup."""
    
    def __init__(self):
        self.premium_db = PREMIUM_DB_FILE
        self.user_requests_db = USER_REQUESTS_DB_FILE
        self.last_sync_time = None
        self.sync_count = 0
    
    def check_prerequisites(self) -> bool:
        """Check if Supabase is available for backup."""
        if not SUPABASE_ENABLED:
            logger.error("❌ Supabase not configured in .env file")
            return False
        
        if not PSYCOPG2_AVAILABLE:
            logger.error("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
            return False
        
        if not os.path.exists(self.premium_db):
            logger.error(f"❌ Premium database not found: {self.premium_db}")
            return False
        
        if not os.path.exists(self.user_requests_db):
            logger.error(f"❌ User requests database not found: {self.user_requests_db}")
            return False
        
        return True
    
    def sync_table(self, sqlite_conn, pg_conn, table_name: str, columns: list) -> dict:
        """
        Sync a single table from SQLite to Supabase.
        
        Strategy: UPSERT (insert or update on conflict)
        """
        return self.sync_table_with_mapping(sqlite_conn, pg_conn, table_name, table_name, columns)
    
    def sync_table_with_mapping(self, sqlite_conn, pg_conn, sqlite_table: str, supabase_table: str, columns: list) -> dict:
        """
        Sync a single table from SQLite to Supabase with different table names.
        
        Strategy: UPSERT (insert or update on conflict)
        """
        try:
            sqlite_cursor = sqlite_conn.cursor()
            pg_cursor = pg_conn.cursor()
            
            # Get all rows from SQLite
            sqlite_cursor.execute(f"SELECT * FROM {sqlite_table}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                logger.info(f"  ℹ️  {sqlite_table} → {supabase_table}: No data to sync")
                return {"synced": 0, "errors": 0}
            
            synced = 0
            errors = 0
            
            # Prepare UPSERT query (PostgreSQL specific)
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join(columns)
            
            # Build conflict resolution based on table
            if supabase_table == 'premium_subscriptions':
                conflict_target = '(owner_id, group_id)'
                update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in ['id']])
            elif supabase_table == 'rate_limit_user_requests':
                conflict_target = '(user_id, chat_id, gift_name)'
                update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in ['user_id', 'chat_id', 'gift_name']])
            elif supabase_table == 'rate_limit_command_requests':
                conflict_target = '(user_id, chat_id, command_name)'
                update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in ['user_id', 'chat_id', 'command_name']])
            elif supabase_table == 'message_owners':
                conflict_target = '(message_id, chat_id)'
                update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in ['message_id', 'chat_id']])
            elif supabase_table == 'refunded_groups':
                conflict_target = '(group_id)'
                update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'group_id'])
            else:
                # Default: use id as conflict target
                conflict_target = '(id)'
                update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'id'])
            
            upsert_query = f"""
                INSERT INTO {supabase_table} ({columns_str})
                VALUES ({placeholders})
                ON CONFLICT {conflict_target}
                DO UPDATE SET {update_set}
            """
            
            # Sync each row
            for row in rows:
                try:
                    pg_cursor.execute(upsert_query, row)
                    synced += 1
                except Exception as e:
                    logger.error(f"  ❌ Error syncing row in {sqlite_table} → {supabase_table}: {e}")
                    errors += 1
            
            pg_conn.commit()
            logger.info(f"  ✅ {sqlite_table} → {supabase_table}: {synced} rows synced, {errors} errors")
            
            return {"synced": synced, "errors": errors}
            
        except Exception as e:
            logger.error(f"  ❌ Error syncing table {sqlite_table} → {supabase_table}: {e}")
            return {"synced": 0, "errors": 1}
    
    def sync_premium_database(self) -> dict:
        """Sync premium_system.db to Supabase."""
        logger.info("📊 Syncing premium database...")
        
        try:
            # Connect to SQLite
            sqlite_conn = sqlite3.connect(self.premium_db)
            
            # Connect to Supabase
            pg_conn = get_connection()
            if not pg_conn:
                logger.error("❌ Failed to connect to Supabase")
                sqlite_conn.close()
                return {"success": False, "error": "Supabase connection failed"}
            
            results = {}
            
            # Sync premium_subscriptions
            results['premium_subscriptions'] = self.sync_table(
                sqlite_conn, pg_conn,
                'premium_subscriptions',
                ['id', 'owner_id', 'group_id', 'payment_id', 'telegram_payment_charge_id', 
                 'stars_amount', 'mrkt_link', 'palace_link', 'tonnel_link', 'portal_link',
                 'created_at', 'expires_at', 'is_active']
            )
            
            # Sync payment_history
            results['payment_history'] = self.sync_table(
                sqlite_conn, pg_conn,
                'payment_history',
                ['id', 'owner_id', 'payment_id', 'stars_amount', 'status', 'created_at']
            )
            
            # Sync refunds
            results['refunds'] = self.sync_table(
                sqlite_conn, pg_conn,
                'refunds',
                ['id', 'owner_id', 'group_id', 'payment_id', 'telegram_payment_charge_id',
                 'reason', 'status', 'created_at', 'processed_at', 'processed_by']
            )
            
            # Sync refunded_groups
            results['refunded_groups'] = self.sync_table(
                sqlite_conn, pg_conn,
                'refunded_groups',
                ['group_id', 'refund_date']
            )
            
            # Close connections
            sqlite_conn.close()
            release_connection(pg_conn)
            
            logger.info("✅ Premium database sync complete")
            return {"success": True, "results": results}
            
        except Exception as e:
            logger.error(f"❌ Premium database sync failed: {e}")
            return {"success": False, "error": str(e)}
    
    def sync_user_requests_database(self) -> dict:
        """Sync user_requests.db to Supabase."""
        logger.info("📊 Syncing user requests database...")
        
        try:
            # Connect to SQLite
            sqlite_conn = sqlite3.connect(self.user_requests_db)
            
            # Connect to Supabase
            pg_conn = get_connection()
            if not pg_conn:
                logger.error("❌ Failed to connect to Supabase")
                sqlite_conn.close()
                return {"success": False, "error": "Supabase connection failed"}
            
            results = {}
            
            # Sync user_requests (SQLite) → rate_limit_user_requests (Supabase)
            results['user_requests'] = self.sync_table_with_mapping(
                sqlite_conn, pg_conn,
                sqlite_table='user_requests',
                supabase_table='rate_limit_user_requests',
                columns=['user_id', 'chat_id', 'gift_name', 'minute']
            )
            
            # Sync command_requests (SQLite) → rate_limit_command_requests (Supabase)
            results['command_requests'] = self.sync_table_with_mapping(
                sqlite_conn, pg_conn,
                sqlite_table='command_requests',
                supabase_table='rate_limit_command_requests',
                columns=['user_id', 'chat_id', 'command_name', 'minute', 'timestamp']
            )
            
            # Sync message_owners
            results['message_owners'] = self.sync_table(
                sqlite_conn, pg_conn,
                'message_owners',
                ['message_id', 'chat_id', 'user_id', 'timestamp']
            )
            
            # Close connections
            sqlite_conn.close()
            release_connection(pg_conn)
            
            logger.info("✅ User requests database sync complete")
            return {"success": True, "results": results}
            
        except Exception as e:
            logger.error(f"❌ User requests database sync failed: {e}")
            return {"success": False, "error": str(e)}
    
    def run_full_sync(self) -> dict:
        """Run a full backup sync to Supabase."""
        logger.info("=" * 60)
        logger.info("🔄 Starting Supabase Backup Sync")
        logger.info(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        # Check prerequisites
        if not self.check_prerequisites():
            logger.error("❌ Prerequisites check failed")
            return {"success": False, "error": "Prerequisites not met"}
        
        # Initialize Supabase tables if needed
        logger.info("🔧 Ensuring Supabase tables exist...")
        if not init_tables():
            logger.error("❌ Failed to initialize Supabase tables")
            return {"success": False, "error": "Table initialization failed"}
        
        # Sync both databases
        premium_result = self.sync_premium_database()
        user_requests_result = self.sync_user_requests_database()
        
        # Update sync stats
        self.last_sync_time = datetime.now()
        self.sync_count += 1
        
        # Summary
        logger.info("=" * 60)
        logger.info("📊 Sync Summary")
        logger.info(f"Premium DB: {'✅ Success' if premium_result['success'] else '❌ Failed'}")
        logger.info(f"User Requests DB: {'✅ Success' if user_requests_result['success'] else '❌ Failed'}")
        logger.info(f"Total Syncs: {self.sync_count}")
        logger.info(f"Last Sync: {self.last_sync_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        return {
            "success": premium_result['success'] and user_requests_result['success'],
            "premium_db": premium_result,
            "user_requests_db": user_requests_result,
            "sync_count": self.sync_count,
            "last_sync_time": self.last_sync_time.isoformat()
        }

def main():
    """Run backup sync once."""
    syncer = SupabaseBackupSync()
    result = syncer.run_full_sync()
    
    if result['success']:
        logger.info("🎉 Backup sync completed successfully!")
        return 0
    else:
        logger.error("❌ Backup sync failed!")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Sync interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
