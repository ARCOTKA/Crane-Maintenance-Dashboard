# SCRIPT NAME: migrate_db.py
# DESCRIPTION: A one-time script to update the database schema without losing crane_stats data.
#              It drops the old service_log table and creates a new one with the correct structure.

import sqlite3
import os

try:
    from paths_updated import DATABASE_PATH
except ImportError:
    # Fallback if run from a different directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, "crane_data.db")

SERVICE_LOG_TABLE_NAME = "service_log"
STATS_TABLE_NAME = "crane_stats"

def migrate():
    """
    Performs a safe migration by replacing the service_log table
    while preserving the crane_stats table.
    """
    print("--- Starting Database Migration ---")
    if not os.path.exists(DATABASE_PATH):
        print(f"Database file not found at {DATABASE_PATH}.")
        print("Please run CraneSats-Zip_db.py first to create the database.")
        return

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        print(f"Successfully connected to {DATABASE_PATH}.")

        # Step 1: Drop the old service_log table. This is where the old service entries are removed.
        print("Attempting to drop the old 'service_log' table...")
        cursor.execute(f"DROP TABLE IF EXISTS {SERVICE_LOG_TABLE_NAME}")
        print("'service_log' table dropped successfully.")

        # Step 2: Create the new service_log table with the 'task_id' column.
        print("Creating new 'service_log' table with the correct 'task_id' column...")
        cursor.execute(f'''
            CREATE TABLE {SERVICE_LOG_TABLE_NAME} (
                id INTEGER PRIMARY KEY,
                crane_number TEXT NOT NULL,
                task_id TEXT NOT NULL,
                service_date TEXT NOT NULL,
                serviced_at_value REAL,
                serviced_by TEXT
            )''')
        print("New 'service_log' table created successfully.")
        
        # Step 3: Verify that the crane_stats table still exists and has data.
        cursor.execute(f"SELECT count(*) FROM {STATS_TABLE_NAME}")
        count = cursor.fetchone()[0]
        print(f"Verification complete: Your '{STATS_TABLE_NAME}' table is safe and contains {count} records.")

        conn.commit()
        conn.close()
        
        print("\n---------------------------------")
        print("--- MIGRATION COMPLETE ---")
        print("---------------------------------")
        print("The database structure has been updated.")
        print("\nNEXT STEPS:")
        print("1. You can now run the main 'dashboard.py' script.")
        print("2. Please use the admin panel in the dashboard to re-enter your two service records.")
        print("---------------------------------")


    except sqlite3.Error as e:
        print(f"\nAn error occurred during migration: {e}")
        print("Please ensure the database file is not locked by another program.")

if __name__ == "__main__":
    migrate()
