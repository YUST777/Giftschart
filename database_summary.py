#!/usr/bin/env python3
import sqlite3
import os

def generate_summary():
    db_path = "/home/yousefmsm1/Desktop/3.7.1/merged_database/merged_user_requests.db"
    
    if not os.path.exists(db_path):
        print("Merged database not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("TELEGRAM BOT DATABASE SUMMARY")
    print("=" * 60)
    
    # Overall statistics
    print("\n📊 OVERALL STATISTICS:")
    print("-" * 30)
    
    cursor.execute("SELECT COUNT(*) FROM user_requests")
    user_requests_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM command_requests")
    command_requests_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM message_owners")
    message_owners_count = cursor.fetchone()[0]
    
    print(f"Total user requests: {user_requests_count:,}")
    print(f"Total command requests: {command_requests_count:,}")
    print(f"Total message owners: {message_owners_count:,}")
    
    # Unique users and groups
    print("\n👥 USERS & GROUPS:")
    print("-" * 30)
    
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_requests")
    unique_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT chat_id) FROM user_requests")
    unique_groups = cursor.fetchone()[0]
    
    print(f"Unique users: {unique_users:,}")
    print(f"Unique groups/chats: {unique_groups:,}")
    
    # Most active users
    print("\n🔥 MOST ACTIVE USERS:")
    print("-" * 30)
    
    cursor.execute("""
        SELECT user_id, COUNT(*) as request_count 
        FROM user_requests 
        GROUP BY user_id 
        ORDER BY request_count DESC 
        LIMIT 10
    """)
    
    top_users = cursor.fetchall()
    for i, (user_id, count) in enumerate(top_users, 1):
        print(f"{i:2d}. User {user_id}: {count:,} requests")
    
    # Most active groups
    print("\n💬 MOST ACTIVE GROUPS:")
    print("-" * 30)
    
    cursor.execute("""
        SELECT chat_id, COUNT(*) as request_count 
        FROM user_requests 
        GROUP BY chat_id 
        ORDER BY request_count DESC 
        LIMIT 10
    """)
    
    top_groups = cursor.fetchall()
    for i, (chat_id, count) in enumerate(top_groups, 1):
        print(f"{i:2d}. Group {chat_id}: {count:,} requests")
    
    # Most popular commands
    print("\n⚡ MOST POPULAR COMMANDS:")
    print("-" * 30)
    
    cursor.execute("""
        SELECT command_name, COUNT(*) as usage_count 
        FROM command_requests 
        GROUP BY command_name 
        ORDER BY usage_count DESC 
        LIMIT 10
    """)
    
    top_commands = cursor.fetchall()
    for i, (command, count) in enumerate(top_commands, 1):
        print(f"{i:2d}. {command}: {count:,} times")
    
    # Most requested gifts
    print("\n🎁 MOST REQUESTED GIFTS:")
    print("-" * 30)
    
    cursor.execute("""
        SELECT gift_name, COUNT(*) as request_count 
        FROM user_requests 
        GROUP BY gift_name 
        ORDER BY request_count DESC 
        LIMIT 10
    """)
    
    top_gifts = cursor.fetchall()
    for i, (gift, count) in enumerate(top_gifts, 1):
        print(f"{i:2d}. {gift}: {count:,} requests")
    
    # Activity by hour
    print("\n⏰ ACTIVITY BY HOUR:")
    print("-" * 30)
    
    cursor.execute("""
        SELECT minute, COUNT(*) as request_count 
        FROM user_requests 
        GROUP BY minute 
        ORDER BY request_count DESC 
        LIMIT 10
    """)
    
    top_hours = cursor.fetchall()
    for i, (minute, count) in enumerate(top_hours, 1):
        hour = minute // 60
        minute_of_hour = minute % 60
        print(f"{i:2d}. {hour:02d}:{minute_of_hour:02d}: {count:,} requests")
    
    # Database size
    print("\n💾 DATABASE SIZE:")
    print("-" * 30)
    
    file_size = os.path.getsize(db_path)
    size_mb = file_size / (1024 * 1024)
    print(f"Database file size: {size_mb:.2f} MB")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("SUMMARY COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    generate_summary() 