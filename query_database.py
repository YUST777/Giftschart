#!/usr/bin/env python3
import sqlite3
import sys

def query_database():
    db_path = "/home/yousefmsm1/Desktop/3.7.1/merged_database/merged_user_requests.db"
    
    if not os.path.exists(db_path):
        print("Merged database not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 DATABASE QUERY TOOL")
    print("=" * 40)
    print("Available queries:")
    print("1. Show total users and groups")
    print("2. Show most active users (top 20)")
    print("3. Show most active groups (top 20)")
    print("4. Show most popular commands")
    print("5. Show most requested gifts")
    print("6. Search for specific user")
    print("7. Search for specific group")
    print("8. Show user activity in a group")
    print("9. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-9): ").strip()
            
            if choice == "1":
                cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_requests")
                users = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(DISTINCT chat_id) FROM user_requests")
                groups = cursor.fetchone()[0]
                print(f"\n📊 Total unique users: {users:,}")
                print(f"📊 Total unique groups: {groups:,}")
                
            elif choice == "2":
                cursor.execute("""
                    SELECT user_id, COUNT(*) as request_count 
                    FROM user_requests 
                    GROUP BY user_id 
                    ORDER BY request_count DESC 
                    LIMIT 20
                """)
                users = cursor.fetchall()
                print("\n🔥 Most Active Users:")
                for i, (user_id, count) in enumerate(users, 1):
                    print(f"{i:2d}. User {user_id}: {count:,} requests")
                    
            elif choice == "3":
                cursor.execute("""
                    SELECT chat_id, COUNT(*) as request_count 
                    FROM user_requests 
                    GROUP BY chat_id 
                    ORDER BY request_count DESC 
                    LIMIT 20
                """)
                groups = cursor.fetchall()
                print("\n💬 Most Active Groups:")
                for i, (chat_id, count) in enumerate(groups, 1):
                    print(f"{i:2d}. Group {chat_id}: {count:,} requests")
                    
            elif choice == "4":
                cursor.execute("""
                    SELECT command_name, COUNT(*) as usage_count 
                    FROM command_requests 
                    GROUP BY command_name 
                    ORDER BY usage_count DESC
                """)
                commands = cursor.fetchall()
                print("\n⚡ Most Popular Commands:")
                for i, (command, count) in enumerate(commands, 1):
                    print(f"{i:2d}. {command}: {count:,} times")
                    
            elif choice == "5":
                cursor.execute("""
                    SELECT gift_name, COUNT(*) as request_count 
                    FROM user_requests 
                    GROUP BY gift_name 
                    ORDER BY request_count DESC
                """)
                gifts = cursor.fetchall()
                print("\n🎁 Most Requested Gifts:")
                for i, (gift, count) in enumerate(gifts, 1):
                    print(f"{i:2d}. {gift}: {count:,} requests")
                    
            elif choice == "6":
                user_id = input("Enter user ID: ").strip()
                try:
                    user_id = int(user_id)
                    cursor.execute("""
                        SELECT chat_id, gift_name, COUNT(*) as request_count 
                        FROM user_requests 
                        WHERE user_id = ? 
                        GROUP BY chat_id, gift_name 
                        ORDER BY request_count DESC
                    """, (user_id,))
                    results = cursor.fetchall()
                    if results:
                        print(f"\n👤 Activity for User {user_id}:")
                        for chat_id, gift, count in results:
                            print(f"  Group {chat_id}: {gift} - {count} requests")
                    else:
                        print(f"No activity found for user {user_id}")
                except ValueError:
                    print("Invalid user ID")
                    
            elif choice == "7":
                chat_id = input("Enter group/chat ID: ").strip()
                try:
                    chat_id = int(chat_id)
                    cursor.execute("""
                        SELECT user_id, gift_name, COUNT(*) as request_count 
                        FROM user_requests 
                        WHERE chat_id = ? 
                        GROUP BY user_id, gift_name 
                        ORDER BY request_count DESC
                    """, (chat_id,))
                    results = cursor.fetchall()
                    if results:
                        print(f"\n💬 Activity in Group {chat_id}:")
                        for user_id, gift, count in results:
                            print(f"  User {user_id}: {gift} - {count} requests")
                    else:
                        print(f"No activity found for group {chat_id}")
                except ValueError:
                    print("Invalid group ID")
                    
            elif choice == "8":
                user_id = input("Enter user ID: ").strip()
                chat_id = input("Enter group/chat ID: ").strip()
                try:
                    user_id = int(user_id)
                    chat_id = int(chat_id)
                    cursor.execute("""
                        SELECT gift_name, COUNT(*) as request_count 
                        FROM user_requests 
                        WHERE user_id = ? AND chat_id = ? 
                        GROUP BY gift_name 
                        ORDER BY request_count DESC
                    """, (user_id, chat_id))
                    results = cursor.fetchall()
                    if results:
                        print(f"\n👤 User {user_id} activity in Group {chat_id}:")
                        for gift, count in results:
                            print(f"  {gift}: {count} requests")
                    else:
                        print(f"No activity found for user {user_id} in group {chat_id}")
                except ValueError:
                    print("Invalid user or group ID")
                    
            elif choice == "9":
                print("Goodbye!")
                break
                
            else:
                print("Invalid choice. Please enter 1-9.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
    
    conn.close()

if __name__ == "__main__":
    import os
    query_database() 