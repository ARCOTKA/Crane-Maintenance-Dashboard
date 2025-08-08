# test_full_refactor.py
import os
import auth
import database
import prediction_engine
from config import Paths, Settings, logger

def run_all_tests():
    """
    Runs a series of checks to verify that all refactored modules
    are correctly using the centralized config.py file.
    """
    logger.info("--- 🚀 Running Full Refactoring Regression Test 🚀 ---")
    tests_passed = 0
    total_tests = 4
    
    # Initialize the database to ensure it's ready for testing
    database.init_db()
    
    # Test 1: File Path check for prediction_engine
    logger.info("1. Testing prediction_engine: Can it find and load service_config.csv?")
    try:
        service_config = prediction_engine.load_service_config()
        if service_config is not None and not service_config.empty:
            logger.info("✅ SUCCESS: prediction_engine loaded service config.")
            tests_passed += 1
        else:
            logger.error("❌ FAILURE: prediction_engine failed to load service config.")
    except Exception as e:
        logger.error(f"❌ FAILURE on prediction_engine test: {e}", exc_info=True)

    # Test 2: File Path check for auth module
    logger.info("2. Testing auth: Can it find and read users.json?")
    try:
        username = auth.verify_admin_password("admin123")
        if username == "admin":
            logger.info("✅ SUCCESS: auth module verified password correctly.")
            tests_passed += 1
        else:
            logger.error("❌ FAILURE: auth module did not verify password correctly.")
    except Exception as e:
        logger.error(f"❌ FAILURE on auth test: {e}", exc_info=True)

    # Test 3: DB Path and Settings check for database module
    logger.info("3. Testing database: Can it connect and query using a configured table name?")
    try:
        windows = database.get_all_maintenance_windows() # This function uses both Paths and Settings
        if windows is not None:
            logger.info("✅ SUCCESS: database module connected and queried successfully.")
            tests_passed += 1
        else:
            logger.error("❌ FAILURE: database module failed on final check.")
    except Exception as e:
        logger.error(f"❌ FAILURE on final database test: {e}", exc_info=True)

    # Test 4: Logging configuration check
    logger.info("4. Testing logger: Is the logger writing to file and console?")
    try:
        log_file_path = Paths.DEBUG_LOG_FILE_PATH
        if os.path.exists(log_file_path) and os.path.getsize(log_file_path) > 0:
            logger.info("✅ SUCCESS: debug.txt exists and is not empty.")
            tests_passed += 1
        else:
            logger.error(f"❌ FAILURE: debug.txt was not found or is empty.")
    except Exception as e:
        logger.error(f"❌ FAILURE on logging test: {e}", exc_info=True)

    # --- FINAL SUMMARY ---
    logger.info("--- 🏁 Test Summary 🏁 ---")
    if tests_passed == total_tests:
        logger.info(f"✅ PASSED: All {tests_passed}/{total_tests} tests were successful.")
    else:
        logger.error(f"❌ FAILED: {total_tests - tests_passed}/{total_tests} tests failed. Please review logs.")

if __name__ == "__main__":
    run_all_tests()
