# SCRIPT NAME: update_db_schema.py
# DESCRIPTION: A one-time script to update the database schema.
# This script adds the 'duration_hours' column to the 'service_log' table
# and creates the 'maintenance_windows' table if they do not already exist.

import sqlite3
import os

try:
    # Import the database path from the central configuration file
    from paths_updated import DATABASE_PATH
except ImportError:
    print("ERROR: 'paths_updated.py' not found. Please ensure it is in the same directory.")
    # Fallback for standalone testing
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, "crane_data.db")

def update_schema():
    """
    Connects to the database and adds the 'duration_hours' column to the
    'service_log' table and creates the 'maintenance_windows' table if they are missing.
    """
    if not os.path.exists(DATABASE_PATH):
        print(f"Database file not found at {DATABASE_PATH}. A new one will be created when you run the dashboard.")
        return

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            # --- Update service_log table ---
            cursor.execute("PRAGMA table_info(service_log)")
            columns = [info[1] for info in cursor.fetchall()]

            if 'duration_hours' not in columns:
                print("Column 'duration_hours' not found in 'service_log' table. Adding it...")
                cursor.execute("ALTER TABLE service_log ADD COLUMN duration_hours REAL")
                conn.commit()
                print("Successfully added 'duration_hours' column to 'service_log' table.")
            else:
                print("Column 'duration_hours' already exists in 'service_log' table. No update needed.")
                
            # --- Create maintenance_windows table if it doesn't exist ---
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='maintenance_windows'")
            if cursor.fetchone() is None:
                print("Table 'maintenance_windows' not found. Creating it...")
                cursor.execute('''
                    CREATE TABLE maintenance_windows (
                        id INTEGER PRIMARY KEY, crane_number TEXT NOT NULL, 
                        from_datetime TEXT NOT NULL, to_datetime TEXT NOT NULL
                    )''')
                conn.commit()
                print("Successfully created 'maintenance_windows' table.")
            else:
                 print("Table 'maintenance_windows' already exists. No update needed.")

    except sqlite3.Error as e:
        print(f"An SQLite error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    print("Running database schema update...")
    update_schema()
    print("Update script finished.")
