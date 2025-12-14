#!/usr/bin/env python3
import sqlite3
import os
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

def create_visual_analytics():
    db_path = "/home/yousefmsm1/Desktop/3.7.1/merged_database/merged_user_requests.db"
    
    if not os.path.exists(db_path):
        print("Merged database not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📊 CREATING VISUAL ANALYTICS...")
    print("=" * 50)
    
    # Set up the plotting style
    plt.style.use('default')
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['font.size'] = 10
    
    # Create output directory for charts
    charts_dir = "/home/yousefmsm1/Desktop/3.7.1/analytics_charts"
    os.makedirs(charts_dir, exist_ok=True)
    
    # 1. HOURLY ACTIVITY CHART
    print("📈 Creating hourly activity chart...")
    cursor.execute("""
        SELECT 
            (minute / 60) as hour,
            COUNT(*) as request_count
        FROM user_requests 
        GROUP BY hour 
        ORDER BY hour
    """)
    hourly_data = cursor.fetchall()
    
    hours = [row[0] for row in hourly_data]
    counts = [row[1] for row in hourly_data]
    
    plt.figure(figsize=(14, 6))
    plt.bar(hours, counts, color='skyblue', alpha=0.7, edgecolor='navy')
    plt.title('📅 Hourly Activity Distribution', fontsize=16, fontweight='bold')
    plt.xlabel('Hour of Day', fontsize=12)
    plt.ylabel('Number of Requests', fontsize=12)
    plt.xticks(range(0, 24))
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{charts_dir}/hourly_activity.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. USER ACTIVITY DISTRIBUTION
    print("👥 Creating user activity distribution chart...")
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
    activity_data = cursor.fetchall()
    
    labels = [row[0] for row in activity_data]
    sizes = [row[1] for row in activity_data]
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc', '#c2c2f0']
    
    plt.figure(figsize=(10, 8))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title('👥 User Activity Distribution', fontsize=16, fontweight='bold')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(f'{charts_dir}/user_activity_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. TOP GROUPS BY ACTIVITY
    print("💬 Creating top groups chart...")
    cursor.execute("""
        SELECT chat_id, COUNT(*) as request_count
        FROM user_requests 
        GROUP BY chat_id 
        ORDER BY request_count DESC 
        LIMIT 15
    """)
    top_groups = cursor.fetchall()
    
    group_ids = [f"Group {row[0]}" for row in top_groups]
    group_counts = [row[1] for row in top_groups]
    
    plt.figure(figsize=(14, 8))
    bars = plt.barh(range(len(group_ids)), group_counts, color='lightcoral', alpha=0.8)
    plt.yticks(range(len(group_ids)), group_ids)
    plt.xlabel('Number of Requests', fontsize=12)
    plt.title('🏆 Top 15 Most Active Groups', fontsize=16, fontweight='bold')
    plt.gca().invert_yaxis()
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        width = bar.get_width()
        plt.text(width + 10, bar.get_y() + bar.get_height()/2, 
                f'{width:,}', ha='left', va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{charts_dir}/top_groups.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. COMMAND USAGE CHART
    print("⚡ Creating command usage chart...")
    cursor.execute("""
        SELECT command_name, COUNT(*) as usage_count
        FROM command_requests 
        GROUP BY command_name 
        ORDER BY usage_count DESC
        LIMIT 15
    """)
    command_data = cursor.fetchall()
    
    commands = [row[0] for row in command_data]
    usages = [row[1] for row in command_data]
    
    plt.figure(figsize=(14, 8))
    bars = plt.barh(range(len(commands)), usages, color='lightgreen', alpha=0.8)
    plt.yticks(range(len(commands)), commands)
    plt.xlabel('Usage Count', fontsize=12)
    plt.title('⚡ Most Popular Commands', fontsize=16, fontweight='bold')
    plt.gca().invert_yaxis()
    
    # Add value labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        plt.text(width + 5, bar.get_y() + bar.get_height()/2, 
                f'{width:,}', ha='left', va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{charts_dir}/command_usage.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 5. GIFT CATEGORIES CHART
    print("🎁 Creating gift categories chart...")
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
    
    categories = [row[0] for row in gift_categories]
    counts = [row[1] for row in gift_categories]
    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
    
    plt.figure(figsize=(10, 8))
    plt.pie(counts, labels=categories, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title('🎁 Gift Categories Distribution', fontsize=16, fontweight='bold')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(f'{charts_dir}/gift_categories.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 6. TOP STICKER COLLECTIONS
    print("🎯 Creating top sticker collections chart...")
    cursor.execute("""
        SELECT gift_name, COUNT(*) as request_count
        FROM user_requests 
        WHERE gift_name LIKE 'sticker_%'
        GROUP BY gift_name 
        ORDER BY request_count DESC
        LIMIT 10
    """)
    sticker_data = cursor.fetchall()
    
    stickers = [row[0].replace('sticker_', '') for row in sticker_data]
    sticker_counts = [row[1] for row in sticker_data]
    
    plt.figure(figsize=(14, 8))
    bars = plt.barh(range(len(stickers)), sticker_counts, color='gold', alpha=0.8)
    plt.yticks(range(len(stickers)), stickers)
    plt.xlabel('Request Count', fontsize=12)
    plt.title('🎯 Top 10 Sticker Collections', fontsize=16, fontweight='bold')
    plt.gca().invert_yaxis()
    
    # Add value labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        plt.text(width + 2, bar.get_y() + bar.get_height()/2, 
                f'{width:,}', ha='left', va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{charts_dir}/top_stickers.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 7. ENGAGEMENT METRICS COMPARISON
    print("📊 Creating engagement metrics chart...")
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_requests")
    unique_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT chat_id) FROM user_requests")
    unique_groups = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM user_requests")
    total_requests = cursor.fetchone()[0]
    
    metrics = ['Total Requests', 'Unique Users', 'Unique Groups']
    values = [total_requests, unique_users, unique_groups]
    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1']
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(metrics, values, color=colors, alpha=0.8)
    plt.title('📊 Key Engagement Metrics', fontsize=16, fontweight='bold')
    plt.ylabel('Count', fontsize=12)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{value:,}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{charts_dir}/engagement_metrics.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 8. USER RETENTION CHART
    print("🔄 Creating user retention chart...")
    cursor.execute("""
        SELECT 
            COUNT(*) as users_with_multiple_requests,
            (SELECT COUNT(DISTINCT user_id) FROM user_requests) as total_users
        FROM (
            SELECT user_id
            FROM user_requests 
            GROUP BY user_id
            HAVING COUNT(*) > 1
        )
    """)
    retention_data = cursor.fetchone()
    
    multiple_users = retention_data[0]
    total_users = retention_data[1]
    single_users = total_users - multiple_users
    
    labels = ['Multiple Requests', 'Single Request']
    sizes = [multiple_users, single_users]
    colors = ['#4ecdc4', '#ff6b6b']
    
    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title('🔄 User Retention Analysis', fontsize=16, fontweight='bold')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(f'{charts_dir}/user_retention.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 9. ACTIVITY BY MINUTE PATTERN
    print("⏰ Creating minute pattern chart...")
    cursor.execute("""
        SELECT 
            (minute % 60) as minute_of_hour,
            COUNT(*) as request_count
        FROM user_requests 
        GROUP BY minute_of_hour
        ORDER BY minute_of_hour
    """)
    minute_data = cursor.fetchall()
    
    minutes = [row[0] for row in minute_data]
    counts = [row[1] for row in minute_data]
    
    plt.figure(figsize=(14, 6))
    plt.plot(minutes, counts, marker='o', linewidth=2, markersize=6, color='purple')
    plt.fill_between(minutes, counts, alpha=0.3, color='purple')
    plt.title('⏰ Activity Pattern by Minute of Hour', fontsize=16, fontweight='bold')
    plt.xlabel('Minute of Hour', fontsize=12)
    plt.ylabel('Number of Requests', fontsize=12)
    plt.xticks(range(0, 60, 5))
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{charts_dir}/minute_pattern.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 10. COMPREHENSIVE SUMMARY CHART
    print("📋 Creating comprehensive summary...")
    
    # Create a summary text file
    summary_file = f'{charts_dir}/analytics_summary.txt'
    with open(summary_file, 'w') as f:
        f.write("🔬 TELEGRAM BOT ANALYTICS SUMMARY\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"📊 OVERALL STATISTICS:\n")
        f.write(f"  Total Requests: {total_requests:,}\n")
        f.write(f"  Unique Users: {unique_users:,}\n")
        f.write(f"  Unique Groups: {unique_groups:,}\n")
        f.write(f"  Average Requests per User: {total_requests/unique_users:.1f}\n")
        f.write(f"  Average Requests per Group: {total_requests/unique_groups:.1f}\n\n")
        
        f.write(f"🔄 RETENTION METRICS:\n")
        f.write(f"  Users with Multiple Requests: {multiple_users:,}\n")
        f.write(f"  Retention Rate: {multiple_users/total_users*100:.1f}%\n\n")
        
        f.write(f"🏆 TOP PERFORMERS:\n")
        f.write(f"  Most Active User: {top_groups[0][0]} ({top_groups[0][1]:,} requests)\n")
        f.write(f"  Most Active Group: {top_groups[0][0]} ({top_groups[0][1]:,} requests)\n")
        f.write(f"  Most Popular Command: {commands[0]} ({usages[0]:,} times)\n\n")
        
        f.write(f"📈 ENGAGEMENT INSIGHTS:\n")
        if hours and counts and len(hours) > 0 and len(counts) > 0:
            max_count = max(counts)
            peak_hour = hours[counts.index(max_count)]
            f.write(f"  Peak Activity Hour: {peak_hour}:00\n")
        if minutes and counts and len(minutes) > 0 and len(counts) > 0:
            max_count = max(counts)
            peak_minute = minutes[counts.index(max_count)]
            f.write(f"  Most Active Minute: {peak_minute}\n")
        if usages and len(usages) > 0:
            f.write(f"  Gift vs Command Ratio: {total_requests/usages[0]:.1f}\n\n")
        
        f.write(f"🎯 RECOMMENDATIONS:\n")
        f.write(f"  1. Focus on peak hours for maximum engagement\n")
        f.write(f"  2. Target users with multiple requests for retention\n")
        f.write(f"  3. Optimize popular sticker collections\n")
        f.write(f"  4. Monitor group activity patterns\n")
        f.write(f"  5. Analyze viral content in top groups\n")
    
    conn.close()
    
    print(f"\n✅ VISUAL ANALYTICS COMPLETE!")
    print(f"📁 Charts saved to: {charts_dir}")
    print(f"📋 Summary saved to: {charts_dir}/analytics_summary.txt")
    print("\n📊 Generated Charts:")
    print("  1. hourly_activity.png - Hourly activity distribution")
    print("  2. user_activity_distribution.png - User engagement levels")
    print("  3. top_groups.png - Most active groups")
    print("  4. command_usage.png - Popular commands")
    print("  5. gift_categories.png - Gift type distribution")
    print("  6. top_stickers.png - Popular sticker collections")
    print("  7. engagement_metrics.png - Key metrics comparison")
    print("  8. user_retention.png - User retention analysis")
    print("  9. minute_pattern.png - Activity by minute pattern")
    print("  10. analytics_summary.txt - Comprehensive summary")

if __name__ == "__main__":
    try:
        create_visual_analytics()
    except ImportError:
        print("❌ matplotlib not installed. Installing...")
        import subprocess
        subprocess.run(["pip3", "install", "matplotlib"])
        print("✅ matplotlib installed. Running analytics...")
        create_visual_analytics() 