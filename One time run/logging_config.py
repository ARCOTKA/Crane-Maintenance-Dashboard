# SCRIPT NAME: logging_config.py
# DESCRIPTION: Centralized configuration for application-wide logging.
# NEW: This is a new file to set up a verbose logger that writes to debug.txt.

import logging
import sys
import os

# --- Path Configuration ---
# To ensure this file can run independently or as part of the app,
# we determine the base directory and the log file path here.
try:
    # Attempt to import the centrally defined path from paths_updated.py
    from paths_updated import DEBUG_LOG_FILE_PATH
except ImportError:
    # This block runs if 'paths_updated.py' is not found.
    # This might happen if you run this script by itself.
    # It defines a fallback path so the script doesn't crash.
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DEBUG_LOG_FILE_PATH = os.path.join(BASE_DIR, "debug.txt")
    print(f"Warning: 'paths_updated.py' not found. Logging to: {DEBUG_LOG_FILE_PATH}")

# --- Logger Setup ---
# We use a single, named logger ("crane_dashboard") throughout the application.
# This allows us to configure it once here and then import it wherever needed.
logger = logging.getLogger("crane_dashboard")
logger.setLevel(logging.DEBUG) # Set the lowest level to capture all messages (DEBUG, INFO, WARNING, ERROR, CRITICAL).

# --- Handler Configuration ---
# Handlers are responsible for sending the log messages to a specific destination.
# We check if handlers already exist to prevent adding them multiple times,
# which can happen if this module is imported more than once.
if not logger.handlers:
    # --- File Handler ---
    # This handler writes log messages to a file.
    try:
        # It will write to 'debug.txt' as defined by DEBUG_LOG_FILE_PATH.
        # mode='w' means the file is overwritten on each new run for a clean slate.
        file_handler = logging.FileHandler(DEBUG_LOG_FILE_PATH, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG) # This handler will capture everything from DEBUG level up.

        # A detailed format for messages written to the log file.
        # Example: 2023-10-27 10:30:00,123 - INFO     - dashboard.setup_ui:55 - UI setup complete.
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)-8s - %(module)s.%(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # If file logging fails (e.g., due to permissions), we print an error
        # but continue, allowing console logging to still work.
        print(f"CRITICAL: Could not set up file logger at {DEBUG_LOG_FILE_PATH}. Error: {e}")

    # --- Console (Stream) Handler ---
    # This handler prints log messages to the console (standard output).
    stream_handler = logging.StreamHandler(sys.stdout)
    # We set this to INFO, so the console isn't cluttered with detailed DEBUG messages.
    # It will only show INFO, WARNING, ERROR, and CRITICAL messages.
    stream_handler.setLevel(logging.INFO)

    # A simpler format for the console output.
    # Example: INFO     - dashboard - Application starting...
    stream_formatter = logging.Formatter('%(levelname)-8s - %(module)s - %(message)s')
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

    logger.info("Logging has been configured successfully.")
    logger.debug(f"Log file path set to: {DEBUG_LOG_FILE_PATH}")
