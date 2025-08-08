# SCRIPT NAME: paths_updated.py
# DESCRIPTION: A centralized configuration file for all important file and directory paths used in the application.
# PURPOSE: Using a central path file makes the application more portable and easier to maintain.
#          If the project folder is moved, or if the file structure changes,
#          paths only need to be updated in this one file.

import os

# --- Base Directory Configuration ---
# This determines the root directory of the project.

# os.path.abspath(__file__) gets the full path to this script (paths_updated.py).
# os.path.dirname(...) gets the directory that contains this script.
# This ensures that all other paths are built relative to the project's location,
# no matter where the project folder is located on the filesystem.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Define All Application Paths Relative to the Base Directory ---

# Path to the directory for log files (not currently used by logging_config, but good practice).
LOG_DIRECTORY = os.path.join(BASE_DIR, "logs")

# Path to the text file containing TAG_IDs to search for in raw data.
TAG_IDS_FILE = os.path.join(BASE_DIR, "TAG_SEARCH.txt")

# Path to the CSV file used for mapping or renaming tags.
TAG_CHANGE_FILE = os.path.join(BASE_DIR, "TAG_CHANGE.csv")

# Path to the JSON file containing user credentials for authentication.
USERS_FILE_PATH = os.path.join(BASE_DIR, "users.json")

# Path to the main SQLite database file.
DATABASE_PATH = os.path.join(BASE_DIR, "crane_data.db")

# Path for a potential Excel report output (not currently used in the dashboard).
OUTPUT_EXCEL_PATH = os.path.join(BASE_DIR, "CraneStats_Report.xlsx")

# Path for a potential PDF report output (not currently used in the dashboard).
OUTPUT_PDF_PATH = os.path.join(BASE_DIR, "CraneStats_Complete_Report.pdf")

# Path to the detailed debug log file, used by logging_config.py.
DEBUG_LOG_FILE_PATH = os.path.join(BASE_DIR, "debug.txt")

# --- Ensure Critical Directories Exist ---
# This piece of code checks if the 'logs' directory exists and creates it if it doesn't.
# This prevents errors that would occur if a script tried to write a file to a non-existent directory.
if not os.path.exists(LOG_DIRECTORY):
    os.makedirs(LOG_DIRECTORY)
    # You could add a log message here, but that might create a circular dependency
    # with the logging_config file. A simple print is fine.
    print(f"Created directory: {LOG_DIRECTORY}")

