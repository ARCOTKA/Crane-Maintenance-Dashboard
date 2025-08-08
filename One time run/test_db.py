import database
from datetime import datetime
import sqlite3
import pandas as pd

# This script will test the foundational database changes.
# It includes a migration step to safely update the database schema
# without losing existing data.

def migrate_database():
    """
    Checks the database schema and migrates the service_log table if needed.
    This is a safe, one-time operation.
    """
    print("--- Checking Database Schema for Migration ---")
    db_path = database.DATABASE_PATH
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if the old 'crane_number' column exists in service_log
        cursor.execute("PRAGMA table_info(service_log)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'crane_number' in columns:
            print("Old schema detected. Starting migration of 'service_log' table...")

            # 1. Read existing data into memory
            print("  Step 1: Backing up existing service log data...")
            old_data_df = pd.read_sql_query("SELECT * FROM service_log", conn)
            print(f"  Found {len(old_data_df)} records to migrate.")

            # 2. Rename the old table
            print("  Step 2: Renaming old table to 'service_log_old'...")
            cursor.execute("ALTER TABLE service_log RENAME TO service_log_old")

            # 3. Re-initialize the database to create the new tables
            print("  Step 3: Creating new tables with updated schema...")
            conn.close() # Close connection before init_db modifies it
            database.init_db()
            conn = sqlite3.connect(db_path) # Reconnect
            cursor = conn.cursor()

            # 4. Insert old data into the new table
            if not old_data_df.empty:
                print("  Step 4: Inserting backed-up data into new 'service_log' table...")
                for index, row in old_data_df.iterrows():
                    cursor.execute(
                        """
                        INSERT INTO service_log (entity_id, entity_type, task_id, service_date, serviced_at_value, serviced_by, duration_hours)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            row['crane_number'],    # Old crane_number goes into entity_id
                            'crane',                # All old records are of type 'crane'
                            row['task_id'],
                            row['service_date'],
                            row.get('serviced_at_value'),
                            row.get('serviced_by'),
                            row.get('duration_hours')
                        )
                    )
                print(f"  Successfully migrated {len(old_data_df)} records.")

            conn.commit()
            print("--- Migration Complete ---")
        else:
            print("Schema is up-to-date. No migration needed.")

    except sqlite3.Error as e:
        print(f"FAILURE: An error occurred during migration: {e}")
    finally:
        conn.close()


def run_test():
    print("\n--- Starting Stage 1 Database Test ---")

    # 1. Initialize or migrate the database
    print("Step 1: Initializing/Migrating database...")
    try:
        # The migrate function will handle both new and old schemas
        migrate_database()
        # We run init_db again just to be sure all tables are present
        database.init_db()
        print("SUCCESS: Database is ready.")
    except Exception as e:
        print(f"FAILURE: Could not prepare database. Error: {e}")
        return

    # 2. Log a test service record for a crane
    print("\nStep 2: Testing service log insertion...")
    test_entity_id = 'RMG01'
    test_entity_type = 'crane'
    test_task_id = 'gantry_brake_check'
    log_id_to_delete = None # Initialize here
    try:
        success = database.log_service_completed(
            entity_id=test_entity_id,
            entity_type=test_entity_type,
            task_id=test_task_id,
            service_date=datetime.now(),
            serviced_at_value=12345.0,
            user='test_user',
            duration_hours=2.5
        )
        if success:
            print(f"SUCCESS: Logged a test service for {test_entity_id}.")
        else:
            print("FAILURE: log_service_completed returned False.")
            return
    except Exception as e:
        print(f"FAILURE: Could not log service. Error: {e}")
        return

    # 3. Retrieve the record we just logged
    print("\nStep 3: Testing service log retrieval...")
    try:
        # Note: get_last_service_record now needs entity_type
        record = database.get_last_service_record(test_entity_id, test_entity_type, test_task_id)
        if record and record.get('serviced_at_value') == 12345.0:
            print(f"SUCCESS: Retrieved the correct test record: {record}")
            log_id_to_delete = record.get('id')
        else:
            print(f"FAILURE: Did not retrieve the correct record. Got: {record}")
            return
    except Exception as e:
        print(f"FAILURE: Could not retrieve service record. Error: {e}")
        return

    # 4. Clean up by deleting the test record
    print("\nStep 4: Testing service log deletion...")
    try:
        if log_id_to_delete:
            delete_success = database.delete_service_log(log_id_to_delete)
            if delete_success:
                print(f"SUCCESS: Deleted test log record with ID {log_id_to_delete}.")
            else:
                print("FAILURE: delete_service_log returned False.")
                return
        else:
            print("SKIPPED: No log ID to delete.")

    except Exception as e:
        print(f"FAILURE: Could not delete service record. Error: {e}")
        return

    print("\n--- Stage 1 Test Complete: All checks passed! ---")

if __name__ == "__main__":
    run_test()
