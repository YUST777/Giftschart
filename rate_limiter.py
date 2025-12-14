# Remove all Supabase imports and wrappers. Only keep the SQLite implementation and local function definitions.
# (The rest of the file is already correct from previous steps.)

import sqlite3
import time
import os
import logging
import datetime

# Integrate premium system for future flexibility (but always enforce rate limit)
try:
    from premium_system import premium_system
except ImportError:
    premium_system = None

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database file
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sqlite_data", "user_requests.db")

def ensure_tables_exist():
    """Check if all required tables exist, and create them if they don't."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_requests'")
    if not cursor.fetchone():
        logger.info("Creating user_requests table")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_requests (
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            gift_name TEXT NOT NULL,
            minute INTEGER NOT NULL,
            PRIMARY KEY (user_id, chat_id, gift_name)
        )
        ''')
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='command_requests'")
    if not cursor.fetchone():
        logger.info("Creating command_requests table")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS command_requests (
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            command_name TEXT NOT NULL,
            minute INTEGER NOT NULL,
            timestamp INTEGER NOT NULL,
            PRIMARY KEY (user_id, chat_id, command_name)
        )
        ''')
    else:
        # Check if timestamp column exists, add it if it doesn't
        cursor.execute("PRAGMA table_info(command_requests)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'timestamp' not in columns:
            logger.info("Adding timestamp column to command_requests table")
            cursor.execute("ALTER TABLE command_requests ADD COLUMN timestamp INTEGER NOT NULL DEFAULT 0")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='message_owners'")
    if not cursor.fetchone():
        logger.info("Creating message_owners table")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_owners (
            message_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            timestamp INTEGER NOT NULL,
            PRIMARY KEY (message_id, chat_id)
        )
        ''')
    conn.commit()
    conn.close()
    logger.info("All required tables verified or created")

def init_db():
    """Initialize the database if it doesn't exist."""
    ensure_tables_exist()

def is_premium_group(chat_id):
    """Check if a group is premium. Always enforce rate limit regardless."""
    if premium_system is not None:
        try:
            return premium_system.is_group_premium(chat_id)
        except Exception:
            return False
    return False

# NOTE: Premium groups are NOT exempt from rate limiting. Strict rate limiting applies to all groups.
def can_user_request(user_id, chat_id, gift_name, cooldown_seconds=None):
    now = datetime.datetime.now()
    current_minute = now.minute
    current_second = now.second
    if not os.path.exists(DB_FILE):
        init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT minute FROM user_requests WHERE user_id = ? AND chat_id = ? AND gift_name = ?", 
        (user_id, chat_id, gift_name)
    )
    result = cursor.fetchone()
    if result:
        last_minute = result[0]
        if last_minute == current_minute:
            seconds_remaining = 60 - current_second
            conn.close()
            return False, seconds_remaining
    cursor.execute(
        "INSERT OR REPLACE INTO user_requests (user_id, chat_id, gift_name, minute) VALUES (?, ?, ?, ?)",
        (user_id, chat_id, gift_name, current_minute)
    )
    conn.commit()
    conn.close()
    return True, 0

def can_user_use_command(user_id, chat_id, command_name):
    current_time = int(time.time())
    
    # Stricter rate limiting for premium buttons to prevent spam
    if command_name in ["premium_button", "premium_info"]:
        cooldown_seconds = 30  # 30 seconds cooldown for premium buttons
    else:
        cooldown_seconds = 60  # 60 seconds for other commands
    
    if not os.path.exists(DB_FILE):
        init_db()
    else:
        ensure_tables_exist()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Use timestamp-based rate limiting for more precision
    cursor.execute(
        "SELECT timestamp FROM command_requests WHERE user_id = ? AND chat_id = ? AND command_name = ?", 
        (user_id, chat_id, command_name)
    )
    result = cursor.fetchone()
    if result:
        last_timestamp = result[0]
        time_diff = current_time - last_timestamp
        if time_diff < cooldown_seconds:
            seconds_remaining = cooldown_seconds - time_diff
            conn.close()
            logger.info(f"Rate limit hit for user {user_id}, command {command_name}: {seconds_remaining}s remaining")
            return False, seconds_remaining
    
    # Update with current timestamp
    cursor.execute(
        "INSERT OR REPLACE INTO command_requests (user_id, chat_id, command_name, minute, timestamp) VALUES (?, ?, ?, ?, ?)",
        (user_id, chat_id, command_name, datetime.datetime.now().minute, current_time)
    )
    conn.commit()
    conn.close()
    logger.info(f"Rate limit passed for user {user_id}, command {command_name}")
    return True, 0

def reset_user_cooldown(user_id, chat_id, gift_name=None):
    if not os.path.exists(DB_FILE):
        return
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if gift_name:
        cursor.execute(
            "DELETE FROM user_requests WHERE user_id = ? AND chat_id = ? AND gift_name = ?",
            (user_id, chat_id, gift_name)
        )
    else:
        cursor.execute(
            "DELETE FROM user_requests WHERE user_id = ? AND chat_id = ?",
            (user_id, chat_id)
        )
    conn.commit()
    conn.close()

def register_message(user_id, chat_id, message_id):
    if not os.path.exists(DB_FILE):
        init_db()
    else:
        ensure_tables_exist()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO message_owners VALUES (?, ?, ?, ?)",
        (message_id, chat_id, user_id, int(time.time()))
    )
    conn.commit()
    conn.close()
    logger.info(f"Registered message {message_id} in chat {chat_id} to user {user_id}")

def register_linked_message(user_id, chat_id, original_message_id, linked_message_id):
    """Register a linked message (like promotion message) that should be deleted with original message"""
    if not os.path.exists(DB_FILE):
        init_db()
    else:
        ensure_tables_exist()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Ensure linked_messages table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS linked_messages (
            original_message_id INTEGER,
            chat_id INTEGER,
            linked_message_id INTEGER,
            user_id INTEGER,
            timestamp INTEGER,
            PRIMARY KEY (original_message_id, chat_id, linked_message_id)
        )
    ''')
    
    cursor.execute(
        "INSERT OR REPLACE INTO linked_messages VALUES (?, ?, ?, ?, ?)",
        (original_message_id, chat_id, linked_message_id, user_id, int(time.time()))
    )
    conn.commit()
    conn.close()
    logger.info(f"Registered linked message {linked_message_id} to original {original_message_id} in chat {chat_id}")

def get_linked_messages(chat_id, original_message_id):
    """Get all linked messages for a given original message"""
    if not os.path.exists(DB_FILE):
        return []
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='linked_messages'")
    if not cursor.fetchone():
        conn.close()
        return []
    
    cursor.execute(
        "SELECT linked_message_id FROM linked_messages WHERE original_message_id = ? AND chat_id = ?",
        (original_message_id, chat_id)
    )
    linked_messages = [row[0] for row in cursor.fetchall()]
    conn.close()
    return linked_messages

def can_delete_message(user_id, chat_id, message_id):
    """
    Check if user can delete this message (owner or admin).
    
    Args:
        user_id: Telegram user ID requesting deletion
        chat_id: Telegram chat ID where the message is
        message_id: ID of the message to delete
        
    Returns:
        bool: True if user is allowed to delete the message
    """
    try:
        # Initialize the database if it doesn't exist
        if not os.path.exists(DB_FILE):
            init_db()
            # New DB won't have any messages registered, but we'll allow deletion for compatibility
            logger.info(f"DB not found, allowing deletion of message {message_id}")
            return True
        else:
            # Ensure the message_owners table exists
            ensure_tables_exist()
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if this message is registered
        cursor.execute(
            "SELECT user_id FROM message_owners WHERE message_id = ? AND chat_id = ?",
            (message_id, chat_id)
        )
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            # Message not in database, allow deletion for compatibility with older messages
            logger.info(f"Message {message_id} not found in database, allowing deletion")
            return True
            
        owner_id = result[0]
        
        # Check if this user is the owner of the message
        # We could add a check for admin status here as well, but for now we'll just check for ownership
        if user_id == owner_id:
            logger.info(f"User {user_id} is authorized to delete message {message_id}")
            return True
        else:
            logger.info(f"User {user_id} is NOT the owner ({owner_id}) of message {message_id}, denying deletion")
            return False
    except Exception as e:
        logger.error(f"Error checking message ownership: {e}")
        # For security, deny access if there's an error checking ownership
        return False

def get_message_owner(chat_id, message_id):
    """Get the user ID of the message owner."""
    try:
        if not os.path.exists(DB_FILE):
            init_db()
            return None
        else:
            ensure_tables_exist()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM message_owners WHERE message_id = ? AND chat_id = ?",
            (message_id, chat_id)
        )
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        return None
    except Exception as e:
        logger.error(f"Error getting message owner: {e}")
        return None

def cleanup_old_message_ownership(max_age_hours=24):
    """
    Clean up old message ownership records to prevent database bloat.
    
    Args:
        max_age_hours: Maximum age in hours for message ownership records (default: 24 hours)
    """
    try:
        if not os.path.exists(DB_FILE):
            return
        
        ensure_tables_exist()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Calculate cutoff timestamp (current time - max_age_hours)
        cutoff_timestamp = int(time.time()) - (max_age_hours * 3600)
        
        # Delete old message ownership records
        cursor.execute(
            "DELETE FROM message_owners WHERE timestamp < ?",
            (cutoff_timestamp,)
        )
        deleted_count = cursor.rowcount
        
        # Delete old linked messages records
        cursor.execute(
            "DELETE FROM linked_messages WHERE timestamp < ?",
            (cutoff_timestamp,)
        )
        deleted_linked_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if deleted_count > 0 or deleted_linked_count > 0:
            logger.info(f"Cleaned up {deleted_count} old message ownership records and {deleted_linked_count} linked message records")
        
    except Exception as e:
        logger.error(f"Error cleaning up old message ownership records: {e}")

def retroactively_register_message(user_id, chat_id, message_id):
    """
    Retroactively register a message with ownership.
    This is useful for messages that might not have been registered when created.
    
    Args:
        user_id: Telegram user ID who should own the message
        chat_id: Telegram chat ID where the message is
        message_id: ID of the message to register
    """
    try:
        if not os.path.exists(DB_FILE):
            init_db()
        else:
            ensure_tables_exist()
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if message already exists
        cursor.execute(
            "SELECT user_id FROM message_owners WHERE message_id = ? AND chat_id = ?",
            (message_id, chat_id)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Message already registered, update ownership if different
            if existing[0] != user_id:
                cursor.execute(
                    "UPDATE message_owners SET user_id = ?, timestamp = ? WHERE message_id = ? AND chat_id = ?",
                    (user_id, int(time.time()), message_id, chat_id)
                )
                logger.info(f"Updated ownership of message {message_id} from user {existing[0]} to user {user_id}")
            else:
                logger.info(f"Message {message_id} already owned by user {user_id}")
        else:
            # Register new message ownership
            cursor.execute(
                "INSERT INTO message_owners VALUES (?, ?, ?, ?)",
                (message_id, chat_id, user_id, int(time.time()))
            )
            logger.info(f"Retroactively registered message {message_id} in chat {chat_id} to user {user_id}")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error retroactively registering message ownership: {e}")
        return False

def get_message_ownership_stats():
    """
    Get statistics about message ownership records.
    
    Returns:
        dict: Statistics about message ownership records
    """
    try:
        if not os.path.exists(DB_FILE):
            return {"total_messages": 0, "total_linked_messages": 0}
        
        ensure_tables_exist()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Count message ownership records
        cursor.execute("SELECT COUNT(*) FROM message_owners")
        total_messages = cursor.fetchone()[0]
        
        # Count linked messages records
        cursor.execute("SELECT COUNT(*) FROM linked_messages")
        total_linked_messages = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_messages": total_messages,
            "total_linked_messages": total_linked_messages
        }
        
    except Exception as e:
        logger.error(f"Error getting message ownership stats: {e}")
        return {"total_messages": 0, "total_linked_messages": 0}
