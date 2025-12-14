#!/usr/bin/env python3
import os
import zipfile
import sqlite3
import tempfile
import shutil
from pathlib import Path
import glob

def merge_databases():
    # Path to the directory containing zip files
    zip_dir = "/home/yousefmsm1/Desktop/3.7.1/huge db files"
    
    # Create output directory for merged database
    output_dir = "/home/yousefmsm1/Desktop/3.7.1/merged_database"
    os.makedirs(output_dir, exist_ok=True)
    
    # Path for the final merged database
    merged_db_path = os.path.join(output_dir, "merged_user_requests.db")
    
    # Create the merged database
    merged_conn = sqlite3.connect(merged_db_path)
    merged_cursor = merged_conn.cursor()
    
    # Create tables in merged database
    merged_cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_requests (
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            gift_name TEXT NOT NULL,
            minute INTEGER NOT NULL,
            PRIMARY KEY (user_id, chat_id, gift_name)
        )
    ''')
    
    merged_cursor.execute('''
        CREATE TABLE IF NOT EXISTS command_requests (
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            command_name TEXT NOT NULL,
            minute INTEGER NOT NULL,
            timestamp INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, chat_id, command_name)
        )
    ''')
    
    merged_cursor.execute('''
        CREATE TABLE IF NOT EXISTS linked_messages (
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            linked_message_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, chat_id, message_id)
        )
    ''')
    
    merged_cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_owners (
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            owner_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, chat_id, message_id)
        )
    ''')
    
    # Get all zip files
    zip_files = glob.glob(os.path.join(zip_dir, "*.zip"))
    print(f"Found {len(zip_files)} zip files to process")
    
    processed_count = 0
    total_records = 0
    
    for zip_file in zip_files:
        try:
            print(f"Processing: {os.path.basename(zip_file)}")
            
            # Extract zip file to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Look for user_requests.db in extracted files
                db_path = os.path.join(temp_dir, "user_requests.db")
                if os.path.exists(db_path):
                    # Connect to the extracted database
                    source_conn = sqlite3.connect(db_path)
                    source_cursor = source_conn.cursor()
                    
                    # Get all tables
                    source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in source_cursor.fetchall()]
                    
                    for table in tables:
                        if table in ['user_requests', 'command_requests', 'linked_messages', 'message_owners']:
                            # Get all data from the table
                            source_cursor.execute(f"SELECT * FROM {table}")
                            rows = source_cursor.fetchall()
                            
                            if rows:
                                # Get column names
                                source_cursor.execute(f"PRAGMA table_info({table})")
                                columns = [row[1] for row in source_cursor.fetchall()]
                                placeholders = ','.join(['?' for _ in columns])
                                
                                # Insert data with conflict resolution (IGNORE to skip duplicates)
                                insert_sql = f"INSERT OR IGNORE INTO {table} VALUES ({placeholders})"
                                merged_cursor.executemany(insert_sql, rows)
                                
                                total_records += len(rows)
                                print(f"  - {table}: {len(rows)} records")
                    
                    source_conn.close()
            
            processed_count += 1
            
        except Exception as e:
            print(f"Error processing {zip_file}: {e}")
            continue
    
    # Commit changes and close connection
    merged_conn.commit()
    merged_conn.close()
    
    print(f"\nMerge completed!")
    print(f"Processed {processed_count} zip files")
    print(f"Total records processed: {total_records}")
    print(f"Merged database saved to: {merged_db_path}")
    
    # Show final statistics
    final_conn = sqlite3.connect(merged_db_path)
    final_cursor = final_conn.cursor()
    
    print("\nFinal database statistics:")
    for table in ['user_requests', 'command_requests', 'linked_messages', 'message_owners']:
        final_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = final_cursor.fetchone()[0]
        print(f"  - {table}: {count} unique records")
    
    # Get unique users and groups
    final_cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_requests")
    unique_users = final_cursor.fetchone()[0]
    
    final_cursor.execute("SELECT COUNT(DISTINCT chat_id) FROM user_requests")
    unique_groups = final_cursor.fetchone()[0]
    
    print(f"\nUnique users: {unique_users}")
    print(f"Unique groups/chats: {unique_groups}")
    
    final_conn.close()

if __name__ == "__main__":
    merge_databases() 