#!/usr/bin/env python3
import sqlite3
import os
from datetime import datetime, timedelta
from collections import Counter, defaultdict

def advanced_analytics():
    db_path = "/home/yousefmsm1/Desktop/3.7.1/merged_database/merged_user_requests.db"
    
    if not os.path.exists(db_path):
        print("Merged database not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔬 ADVANCED DATABASE ANALYTICS")
    print("=" * 60)
    
    # 1. TIME-BASED ANALYSIS
    print("\n📅 TIME-BASED ANALYSIS:")
    print("-" * 40)
    
    # Hourly activity distribution
    cursor.execute("""
        SELECT 
            (minute / 60) as hour,
            COUNT(*) as request_count
        FROM user_requests 
        GROUP BY hour 
        ORDER BY hour
    """)
    hourly_data = cursor.fetchall()
    
    print("🕐 Hourly Activity Distribution:")
    for hour, count in hourly_data:
        print(f"  {hour:02d}:00 - {hour:02d}:59: {count:,} requests")
    
    # Peak activity hours
    cursor.execute("""
        SELECT 
            (minute / 60) as hour,
            COUNT(*) as request_count
        FROM user_requests 
        GROUP BY hour 
        ORDER BY request_count DESC 
        LIMIT 5
    """)
    peak_hours = cursor.fetchall()
    print(f"\n🔥 Peak Activity Hours:")
    for hour, count in peak_hours:
        print(f"  {hour:02d}:00 - {hour:02d}:59: {count:,} requests")
    
    # 2. USER ENGAGEMENT ANALYSIS
    print("\n👥 USER ENGAGEMENT ANALYSIS:")
    print("-" * 40)
    
    # User activity distribution
    cursor.execute("""
        SELECT 
            CASE 
                WHEN request_count = 1 THEN '1 request'
                WHEN request_count BETWEEN 2 AND 5 THEN '2-5 requests'
                WHEN request_count BETWEEN 6 AND 10 THEN '6-10 requests'
                WHEN request_count BETWEEN 11 AND 20 THEN '11-20 requests'
                WHEN request_count BETWEEN 21 AND 50 THEN '21-50 requests'
                ELSE '50+ requests'
            END as activity_level,
            COUNT(*) as user_count
        FROM (
            SELECT user_id, COUNT(*) as request_count
            FROM user_requests 
            GROUP BY user_id
        )
        GROUP BY activity_level
        ORDER BY user_count DESC
    """)
    activity_distribution = cursor.fetchall()
    
    print("📊 User Activity Distribution:")
    for level, count in activity_distribution:
        print(f"  {level}: {count:,} users")
    
    # Power users (users with 50+ requests)
    cursor.execute("""
        SELECT user_id, COUNT(*) as request_count
        FROM user_requests 
        GROUP BY user_id 
        HAVING COUNT(*) >= 50
        ORDER BY request_count DESC
    """)
    power_users = cursor.fetchall()
    print(f"\n💪 Power Users (50+ requests): {len(power_users)} users")
    for user_id, count in power_users[:10]:
        print(f"  User {user_id}: {count:,} requests")
    
    # 3. GROUP ANALYSIS
    print("\n💬 GROUP ANALYSIS:")
    print("-" * 40)
    
    # Group activity distribution
    cursor.execute("""
        SELECT 
            CASE 
                WHEN request_count < 10 THEN '< 10 requests'
                WHEN request_count BETWEEN 10 AND 50 THEN '10-50 requests'
                WHEN request_count BETWEEN 51 AND 100 THEN '51-100 requests'
                WHEN request_count BETWEEN 101 AND 500 THEN '101-500 requests'
                ELSE '500+ requests'
            END as activity_level,
            COUNT(*) as group_count
        FROM (
            SELECT chat_id, COUNT(*) as request_count
            FROM user_requests 
            GROUP BY chat_id
        )
        GROUP BY activity_level
        ORDER BY group_count DESC
    """)
    group_distribution = cursor.fetchall()
    
    print("📊 Group Activity Distribution:")
    for level, count in group_distribution:
        print(f"  {level}: {count:,} groups")
    
    # Most active groups with user count
    cursor.execute("""
        SELECT 
            ur.chat_id,
            COUNT(DISTINCT ur.user_id) as unique_users,
            COUNT(*) as total_requests
        FROM user_requests ur
        GROUP BY ur.chat_id
        ORDER BY total_requests DESC
        LIMIT 15
    """)
    top_groups = cursor.fetchall()
    
    print(f"\n🏆 Top Groups by Activity:")
    for chat_id, users, requests in top_groups:
        print(f"  Group {chat_id}: {requests:,} requests by {users:,} users")
    
    # 4. COMMAND ANALYSIS
    print("\n⚡ COMMAND ANALYSIS:")
    print("-" * 40)
    
    # Command usage patterns
    cursor.execute("""
        SELECT 
            command_name,
            COUNT(*) as usage_count,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT chat_id) as unique_groups
        FROM command_requests 
        GROUP BY command_name 
        ORDER BY usage_count DESC
    """)
    command_stats = cursor.fetchall()
    
    print("📊 Command Usage Statistics:")
    for command, usage, users, groups in command_stats:
        print(f"  {command}:")
        print(f"    Usage: {usage:,} times")
        print(f"    Users: {users:,}")
        print(f"    Groups: {groups:,}")
    
    # 5. GIFT/STICKER ANALYSIS
    print("\n🎁 GIFT/STICKER ANALYSIS:")
    print("-" * 40)
    
    # Gift categories
    cursor.execute("""
        SELECT 
            CASE 
                WHEN gift_name LIKE 'gift_%' THEN 'Gift Items'
                WHEN gift_name LIKE 'sticker_%' THEN 'Sticker Collections'
                WHEN gift_name LIKE 'start%' THEN 'Start Commands'
                ELSE 'Other Items'
            END as category,
            COUNT(*) as request_count
        FROM user_requests 
        GROUP BY category
        ORDER BY request_count DESC
    """)
    gift_categories = cursor.fetchall()
    
    print("📊 Gift Categories:")
    for category, count in gift_categories:
        print(f"  {category}: {count:,} requests")
    
    # Top sticker collections
    cursor.execute("""
        SELECT gift_name, COUNT(*) as request_count
        FROM user_requests 
        WHERE gift_name LIKE 'sticker_%'
        GROUP BY gift_name 
        ORDER BY request_count DESC
        LIMIT 15
    """)
    top_stickers = cursor.fetchall()
    
    print(f"\n🎯 Top Sticker Collections:")
    for sticker, count in top_stickers:
        print(f"  {sticker}: {count:,} requests")
    
    # 6. USER-GROUP INTERACTION ANALYSIS
    print("\n🤝 USER-GROUP INTERACTION ANALYSIS:")
    print("-" * 40)
    
    # Users active in multiple groups
    cursor.execute("""
        SELECT 
            user_id,
            COUNT(DISTINCT chat_id) as group_count,
            COUNT(*) as total_requests
        FROM user_requests 
        GROUP BY user_id
        HAVING COUNT(DISTINCT chat_id) > 1
        ORDER BY group_count DESC, total_requests DESC
        LIMIT 10
    """)
    multi_group_users = cursor.fetchall()
    
    print("🌐 Users Active in Multiple Groups:")
    for user_id, groups, requests in multi_group_users:
        print(f"  User {user_id}: {groups} groups, {requests:,} total requests")
    
    # 7. ENGAGEMENT METRICS
    print("\n📈 ENGAGEMENT METRICS:")
    print("-" * 40)
    
    # Average requests per user
    cursor.execute("""
        SELECT 
            COUNT(*) as total_requests,
            COUNT(DISTINCT user_id) as unique_users,
            ROUND(CAST(COUNT(*) AS FLOAT) / COUNT(DISTINCT user_id), 2) as avg_requests_per_user
        FROM user_requests
    """)
    engagement_stats = cursor.fetchone()
    
    print(f"📊 Overall Engagement:")
    print(f"  Total requests: {engagement_stats[0]:,}")
    print(f"  Unique users: {engagement_stats[1]:,}")
    print(f"  Average requests per user: {engagement_stats[2]}")
    
    # Average requests per group
    cursor.execute("""
        SELECT 
            COUNT(*) as total_requests,
            COUNT(DISTINCT chat_id) as unique_groups,
            ROUND(CAST(COUNT(*) AS FLOAT) / COUNT(DISTINCT chat_id), 2) as avg_requests_per_group
        FROM user_requests
    """)
    group_engagement = cursor.fetchone()
    
    print(f"\n📊 Group Engagement:")
    print(f"  Total requests: {group_engagement[0]:,}")
    print(f"  Unique groups: {group_engagement[1]:,}")
    print(f"  Average requests per group: {group_engagement[2]}")
    
    # 8. RETENTION ANALYSIS
    print("\n🔄 RETENTION ANALYSIS:")
    print("-" * 40)
    
    # Users with multiple requests
    cursor.execute("""
        SELECT 
            COUNT(*) as users_with_multiple_requests,
            (SELECT COUNT(DISTINCT user_id) FROM user_requests) as total_users,
            ROUND(CAST(COUNT(*) AS FLOAT) / (SELECT COUNT(DISTINCT user_id) FROM user_requests) * 100, 2) as retention_rate
        FROM (
            SELECT user_id
            FROM user_requests 
            GROUP BY user_id
            HAVING COUNT(*) > 1
        )
    """)
    retention_stats = cursor.fetchone()
    
    print(f"📊 User Retention:")
    print(f"  Users with multiple requests: {retention_stats[0]:,}")
    print(f"  Total unique users: {retention_stats[1]:,}")
    print(f"  Retention rate: {retention_stats[2]}%")
    
    # 9. SEASONAL PATTERNS
    print("\n🌍 SEASONAL PATTERNS:")
    print("-" * 40)
    
    # Activity by minute (to see patterns within hours)
    cursor.execute("""
        SELECT 
            (minute % 60) as minute_of_hour,
            COUNT(*) as request_count
        FROM user_requests 
        GROUP BY minute_of_hour
        ORDER BY request_count DESC
        LIMIT 10
    """)
    minute_patterns = cursor.fetchall()
    
    print("⏰ Most Active Minutes of the Hour:")
    for minute, count in minute_patterns:
        print(f"  Minute {minute}: {count:,} requests")
    
    # 10. CROSS-PLATFORM ANALYSIS
    print("\n🔗 CROSS-PLATFORM ANALYSIS:")
    print("-" * 40)
    
    # Commands vs Gift requests ratio
    cursor.execute("SELECT COUNT(*) FROM command_requests")
    command_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM user_requests")
    gift_count = cursor.fetchone()[0]
    
    print(f"📊 Command vs Gift Requests:")
    print(f"  Command requests: {command_count:,}")
    print(f"  Gift requests: {gift_count:,}")
    print(f"  Ratio: {gift_count/command_count:.2f} gift requests per command")
    
    # 11. VIRAL CONTENT ANALYSIS
    print("\n🦠 VIRAL CONTENT ANALYSIS:")
    print("-" * 40)
    
    # Most requested items in single groups
    cursor.execute("""
        SELECT 
            chat_id,
            gift_name,
            COUNT(*) as request_count
        FROM user_requests 
        GROUP BY chat_id, gift_name
        ORDER BY request_count DESC
        LIMIT 10
    """)
    viral_items = cursor.fetchall()
    
    print("🔥 Most Viral Items by Group:")
    for chat_id, gift, count in viral_items:
        print(f"  Group {chat_id}: {gift} - {count:,} requests")
    
    # 12. USER BEHAVIOR PATTERNS
    print("\n🧠 USER BEHAVIOR PATTERNS:")
    print("-" * 40)
    
    # Users who request multiple different items
    cursor.execute("""
        SELECT 
            user_id,
            COUNT(DISTINCT gift_name) as unique_items,
            COUNT(*) as total_requests
        FROM user_requests 
        GROUP BY user_id
        HAVING COUNT(DISTINCT gift_name) > 1
        ORDER BY unique_items DESC, total_requests DESC
        LIMIT 10
    """)
    diverse_users = cursor.fetchall()
    
    print("🎨 Users with Diverse Requests:")
    for user_id, items, requests in diverse_users:
        print(f"  User {user_id}: {items} different items, {requests:,} total requests")
    
    # 13. GROWTH ANALYSIS
    print("\n📈 GROWTH ANALYSIS:")
    print("-" * 40)
    
    # Activity by time periods (assuming minute represents time)
    cursor.execute("""
        SELECT 
            CASE 
                WHEN minute < 1000 THEN 'Early Period'
                WHEN minute < 2000 THEN 'Mid Period'
                ELSE 'Recent Period'
            END as time_period,
            COUNT(*) as request_count
        FROM user_requests 
        GROUP BY time_period
        ORDER BY request_count DESC
    """)
    growth_periods = cursor.fetchall()
    
    print("📊 Activity by Time Periods:")
    for period, count in growth_periods:
        print(f"  {period}: {count:,} requests")
    
    # 14. COMPETITIVE ANALYSIS
    print("\n🏆 COMPETITIVE ANALYSIS:")
    print("-" * 40)
    
    # Most competitive groups (highest unique users)
    cursor.execute("""
        SELECT 
            chat_id,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(*) as total_requests
        FROM user_requests 
        GROUP BY chat_id
        ORDER BY unique_users DESC
        LIMIT 10
    """)
    competitive_groups = cursor.fetchall()
    
    print("🥇 Most Competitive Groups (by unique users):")
    for chat_id, users, requests in competitive_groups:
        print(f"  Group {chat_id}: {users:,} users, {requests:,} requests")
    
    # 15. FINAL SUMMARY
    print("\n🎯 FINAL SUMMARY:")
    print("-" * 40)
    
    total_requests = engagement_stats[0]
    unique_users = engagement_stats[1]
    unique_groups = group_engagement[1]
    
    print(f"📊 Key Metrics:")
    print(f"  Total bot interactions: {total_requests:,}")
    print(f"  Unique users reached: {unique_users:,}")
    print(f"  Groups/chats served: {unique_groups:,}")
    print(f"  Average engagement: {total_requests/unique_users:.1f} requests per user")
    print(f"  Group penetration: {unique_groups} groups")
    print(f"  User retention: {retention_stats[2]}%")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("ANALYTICS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    advanced_analytics() 