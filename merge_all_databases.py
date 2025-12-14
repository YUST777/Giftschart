#!/usr/bin/env python3
import os
import zipfile
import sqlite3
import tempfile
import glob

def merge_all_databases():
    # Path to the directory containing zip files
    zip_dir = "/home/yousefmsm1/Desktop/3.7.1/huge db files"
    
    # Create output directory for merged databases
    output_dir = "/home/yousefmsm1/Desktop/3.7.1/merged_database"
    os.makedirs(output_dir, exist_ok=True)
    
    # Database files to merge
    db_files = [
        "user_requests.db",
        "analytics.db", 
        "bypass_stats.db",
        "premium_system.db",
        "historical_prices.db"
    ]
    
    # Get all zip files
    zip_files = glob.glob(os.path.join(zip_dir, "*.zip"))
    print(f"Found {len(zip_files)} zip files to process")
    
    # Process each database type
    for db_name in db_files:
        print(f"\n🔄 Processing {db_name}...")
        
        # Path for the merged database
        merged_db_path = os.path.join(output_dir, f"merged_{db_name}")
        
        # Create the merged database
        merged_conn = sqlite3.connect(merged_db_path)
        merged_cursor = merged_conn.cursor()
        
        processed_count = 0
        total_records = 0
        
        for zip_file in zip_files:
            try:
                # Extract zip file to temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    # Look for the specific database in extracted files
                    db_path = os.path.join(temp_dir, db_name)
                    if os.path.exists(db_path):
                        # Connect to the extracted database
                        source_conn = sqlite3.connect(db_path)
                        source_cursor = source_conn.cursor()
                        
                        # Get all tables
                        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = [row[0] for row in source_cursor.fetchall()]
                        
                        for table in tables:
                            # Get all data from the table
                            source_cursor.execute(f"SELECT * FROM {table}")
                            rows = source_cursor.fetchall()
                            
                            if rows:
                                # Get column names
                                source_cursor.execute(f"PRAGMA table_info({table})")
                                columns = [row[1] for row in source_cursor.fetchall()]
                                placeholders = ','.join(['?' for _ in columns])
                                
                                # Create table if it doesn't exist
                                source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
                                create_sql = source_cursor.fetchone()[0]
                                merged_cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} AS SELECT * FROM (SELECT 1) WHERE 0")
                                
                                # Insert data with conflict resolution (IGNORE to skip duplicates)
                                insert_sql = f"INSERT OR IGNORE INTO {table} VALUES ({placeholders})"
                                merged_cursor.executemany(insert_sql, rows)
                                
                                total_records += len(rows)
                        
                        source_conn.close()
                
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing {zip_file}: {e}")
                continue
        
        # Commit changes and close connection
        merged_conn.commit()
        merged_conn.close()
        
        print(f"✅ {db_name} merge completed!")
        print(f"   Processed {processed_count} zip files")
        print(f"   Total records: {total_records}")
        print(f"   Saved to: {merged_db_path}")

if __name__ == "__main__":
    merge_all_databases() 