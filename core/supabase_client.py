#!/usr/bin/env python3
"""
Supabase Database Client for GiftsChart Bot

This module provides PostgreSQL database access via Supabase.
Replaces SQLite for production scalability.
"""

import os
import sys
from typing import Optional, Dict, List, Any
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_DB_HOST = os.getenv("SUPABASE_DB_HOST")
SUPABASE_DB_PORT = os.getenv("SUPABASE_DB_PORT", "5432")
SUPABASE_DB_NAME = os.getenv("SUPABASE_DB_NAME", "postgres")
SUPABASE_DB_USER = os.getenv("SUPABASE_DB_USER")
SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")

# Check if Supabase is configured
SUPABASE_ENABLED = all([
    SUPABASE_DB_HOST,
    SUPABASE_DB_USER,
    SUPABASE_DB_PASSWORD
])

if SUPABASE_ENABLED:
    try:
        import psycopg2
        from psycopg2 import pool
        PSYCOPG2_AVAILABLE = True
        logger.info("✅ Supabase PostgreSQL client available")
    except ImportError:
        PSYCOPG2_AVAILABLE = False
        logger.warning("⚠️  psycopg2 not installed. Install with: pip install psycopg2-binary")
else:
    PSYCOPG2_AVAILABLE = False
    logger.info("ℹ️  Supabase not configured, using SQLite fallback")

# Connection pool
_connection_pool = None

def get_connection_pool():
    """Get or create PostgreSQL connection pool."""
    global _connection_pool
    
    if not SUPABASE_ENABLED or not PSYCOPG2_AVAILABLE:
        return None
    
    if _connection_pool is None:
        try:
            _connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=SUPABASE_DB_HOST,
                port=SUPABASE_DB_PORT,
                database=SUPABASE_DB_NAME,
                user=SUPABASE_DB_USER,
                password=SUPABASE_DB_PASSWORD,
                sslmode='require'
            )
            logger.info("✅ Supabase connection pool created")
        except Exception as e:
            logger.error(f"❌ Failed to create Supabase connection pool: {e}")
            return None
    
    return _connection_pool

def get_connection():
    """Get a connection from the pool."""
    pool = get_connection_pool()
    if pool:
        try:
            return pool.getconn()
        except Exception as e:
            logger.error(f"❌ Failed to get connection from pool: {e}")
            return None
    return None

def release_connection(conn):
    """Release a connection back to the pool."""
    pool = get_connection_pool()
    if pool and conn:
        try:
            pool.putconn(conn)
        except Exception as e:
            logger.error(f"❌ Failed to release connection: {e}")

def execute_query(query: str, params: tuple = None, fetch: bool = False) -> Optional[Any]:
    """
    Execute a SQL query on Supabase.
    
    Args:
        query: SQL query string
        params: Query parameters (tuple)
        fetch: Whether to fetch results
        
    Returns:
        Query results if fetch=True, None otherwise
    """
    if not SUPABASE_ENABLED or not PSYCOPG2_AVAILABLE:
        return None
    
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if fetch:
            results = cursor.fetchall()
            cursor.close()
            conn.commit()
            release_connection(conn)
            return results
        else:
            conn.commit()
            cursor.close()
            release_connection(conn)
            return True
            
    except Exception as e:
        logger.error(f"❌ Query execution failed: {e}")
        if conn:
            conn.rollback()
            release_connection(conn)
        return None

def init_tables():
    """Initialize Supabase tables (same schema as SQLite)."""
    if not SUPABASE_ENABLED or not PSYCOPG2_AVAILABLE:
        logger.info("Supabase not available, skipping table initialization")
        return False
    
    logger.info("Initializing Supabase tables...")
    
    # Premium subscriptions table (matches SQLite schema exactly)
    premium_table = """
    CREATE TABLE IF NOT EXISTS premium_subscriptions (
        id SERIAL PRIMARY KEY,
        owner_id BIGINT NOT NULL,
        group_id BIGINT NOT NULL,
        payment_id TEXT NOT NULL,
        telegram_payment_charge_id TEXT NOT NULL,
        stars_amount INTEGER NOT NULL,
        mrkt_link TEXT,
        palace_link TEXT,
        tonnel_link TEXT,
        portal_link TEXT,
        created_at BIGINT NOT NULL,
        expires_at BIGINT,
        is_active BOOLEAN DEFAULT TRUE,
        UNIQUE(owner_id, group_id)
    );
    CREATE INDEX IF NOT EXISTS idx_premium_group_id ON premium_subscriptions(group_id);
    CREATE INDEX IF NOT EXISTS idx_premium_owner_id ON premium_subscriptions(owner_id);
    """
    
    # User requests table (rate limiting)
    user_requests_table = """
    CREATE TABLE IF NOT EXISTS user_requests (
        user_id BIGINT NOT NULL,
        chat_id BIGINT NOT NULL,
        gift_name TEXT NOT NULL,
        minute BIGINT NOT NULL,
        PRIMARY KEY (user_id, chat_id, gift_name)
    );
    CREATE INDEX IF NOT EXISTS idx_user_requests_minute ON user_requests(minute);
    """
    
    # Command requests table
    command_requests_table = """
    CREATE TABLE IF NOT EXISTS command_requests (
        user_id BIGINT NOT NULL,
        chat_id BIGINT NOT NULL,
        command_name TEXT NOT NULL,
        minute BIGINT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, chat_id, command_name, minute)
    );
    """
    
    # Message owners table
    message_owners_table = """
    CREATE TABLE IF NOT EXISTS message_owners (
        user_id BIGINT NOT NULL,
        chat_id BIGINT NOT NULL,
        message_id BIGINT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, chat_id, message_id)
    );
    """
    
    # Payment history table
    payment_history_table = """
    CREATE TABLE IF NOT EXISTS payment_history (
        id SERIAL PRIMARY KEY,
        owner_id BIGINT NOT NULL,
        payment_id TEXT NOT NULL,
        stars_amount INTEGER NOT NULL,
        status TEXT NOT NULL,
        created_at BIGINT NOT NULL
    );
    """
    
    # Refunds table (matches SQLite schema)
    refunds_table = """
    CREATE TABLE IF NOT EXISTS refunds (
        id SERIAL PRIMARY KEY,
        owner_id BIGINT NOT NULL,
        group_id BIGINT NOT NULL,
        payment_id TEXT NOT NULL,
        telegram_payment_charge_id TEXT,
        reason TEXT,
        status TEXT DEFAULT 'pending',
        created_at BIGINT NOT NULL,
        processed_at BIGINT,
        processed_by TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_refunds_status ON refunds(status);
    """
    
    # Refunded groups table (matches SQLite schema)
    refunded_groups_table = """
    CREATE TABLE IF NOT EXISTS refunded_groups (
        group_id BIGINT PRIMARY KEY,
        refund_date BIGINT NOT NULL
    );
    """
    
    tables = [
        premium_table,
        user_requests_table,
        command_requests_table,
        message_owners_table,
        payment_history_table,
        refunds_table,
        refunded_groups_table
    ]
    
    for table_sql in tables:
        if not execute_query(table_sql):
            logger.error(f"Failed to create table")
            return False
    
    logger.info("✅ All Supabase tables initialized")
    return True

def test_connection() -> bool:
    """Test Supabase connection."""
    if not SUPABASE_ENABLED or not PSYCOPG2_AVAILABLE:
        return False
    
    try:
        result = execute_query("SELECT 1", fetch=True)
        if result:
            logger.info("✅ Supabase connection test successful")
            return True
        else:
            logger.error("❌ Supabase connection test failed")
            return False
    except Exception as e:
        logger.error(f"❌ Supabase connection test error: {e}")
        return False

# Auto-initialize on import
if SUPABASE_ENABLED and PSYCOPG2_AVAILABLE:
    logger.info("Supabase client initialized")
else:
    logger.info("Supabase client not available, using SQLite fallback")
