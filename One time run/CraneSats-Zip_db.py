# SCRIPT NAME: CraneSats-Zip_db_FIXED.py
# DESCRIPTION: A more robust version of the data collector that parses crane logs
#              and saves the data to an SQLite database.
# NEW: Implemented a comprehensive logging system to create a debug.txt file for diagnostics.

import sys
import os
import re
import zipfile
import time
import pandas as pd
import logging

# --- Use the updated paths file and import the database module ---
try:
    from paths_updated import LOG_DIRECTORY, TAG_IDS_FILE, TAG_CHANGE_FILE, DEBUG_LOG_FILE_PATH
    import database
except ImportError:
    print("ERROR: 'paths_updated.py' or 'database.py' not found. Please ensure they are in the same directory.")
    sys.exit(1)

# --- NEW: Setup comprehensive logging ---
# This will create a debug.txt file with detailed information.
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=DEBUG_LOG_FILE_PATH,
    filemode='w' # 'w' overwrites the file each time, 'a' appends
)
# Also, print INFO level messages and above to the console
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger('').addHandler(console_handler)


# --- Configuration ---
NUM_RECENT_FILES = 9999
CRANE_STATISTIC_TYPE = "Perma"
RMG_START_NUM = 1
RMG_END_NUM = 12

# --- Main Script Logic ---
logging.info("Starting log analysis with FIXED parser and debug logging...")
start_time = time.time()

database.init_db()

# Read TAG_IDs
tag_ids = []
if os.path.exists(TAG_IDS_FILE):
    with open(TAG_IDS_FILE, 'r') as f:
        tag_ids = [line.strip() for line in f if line.strip()]
else:
    logging.error(f"Error: TAG_IDs file '{TAG_IDS_FILE}' not found.")
    sys.exit(1)

# Load TAG_CHANGE mapping
tag_mapping = {}
if os.path.exists(TAG_CHANGE_FILE):
    try:
        df_tag_change = pd.read_csv(TAG_CHANGE_FILE)
        df_tag_change['TAG_CLEANED'] = df_tag_change['TAG'].astype(str).apply(lambda x: re.sub(r'[^\x20-\x7E]', '', x).strip())
        df_tag_change['FV_CLEANED'] = df_tag_change['FV'].astype(str).apply(lambda x: re.sub(r'[^\x20-\x7E]', '', x).strip())
        tag_mapping = df_tag_change.set_index('TAG_CLEANED')['FV_CLEANED'].to_dict()
    except Exception as e:
        logging.error(f"Error reading TAG_CHANGE file '{TAG_CHANGE_FILE}': {e}")

# Generate search patterns
BASE_SEARCH_PATTERN_TEMPLATE = "TAG:[RMG{0:02d}/RMG{0:02d}:CRANE.STATISTIC.{1}.{2}]"
search_patterns = [BASE_SEARCH_PATTERN_TEMPLATE.format(i, CRANE_STATISTIC_TYPE, tag_id) for i in range(RMG_START_NUM, RMG_END_NUM + 1) for tag_id in tag_ids]

logging.info(f"Scanning directory: \"{LOG_DIRECTORY}\" for log files.")
if not os.path.isdir(LOG_DIRECTORY):
    logging.error(f"Error: Log directory '{LOG_DIRECTORY}' not found.")
    sys.exit(1)

files_to_process_info = [{'path': os.path.join(LOG_DIRECTORY, f), 'mtime': os.path.getmtime(os.path.join(LOG_DIRECTORY, f))} for f in os.listdir(LOG_DIRECTORY) if os.path.isfile(os.path.join(LOG_DIRECTORY, f)) and (f.lower().endswith('.zip') or f.lower().endswith('.log'))]
files_to_process_info.sort(key=lambda x: x['mtime'], reverse=True)
files_to_process = files_to_process_info[:NUM_RECENT_FILES]

# --- Main Parsing Loop ---
for file_info in files_to_process:
    current_file_path = file_info['path']
    file_extension = os.path.splitext(current_file_path)[1].lower()
    
    def process_line(line, line_num):
        # Check if any of our target patterns are in the line
        if any(pattern in line for pattern in search_patterns):
            logging.debug(f"L{line_num}: Found potential match: {line.strip()}")
            
            match = re.match(r'^(.*?): \(\d+\): (TAG:\[[^\]]+\])\s*(.*)$', line.strip())
            if match:
                timestamp_str, full_tag_string, result_str = match.groups()
                crane_match = re.search(r'TAG:\[(RMG\d{2})/', full_tag_string)
                if crane_match:
                    crane_number = crane_match.group(1)
                    prefix = f"TAG:[{crane_number}/{crane_number}:CRANE.STATISTIC.{CRANE_STATISTIC_TYPE}."
                    tag_detail_match = re.search(rf'{re.escape(prefix)}([^\]]+)\]', full_tag_string)
                    if tag_detail_match:
                        tag_detail_cleaned = re.sub(r'[^\x20-\x7E]', '', tag_detail_match.group(1).strip()).strip()
                        human_readable_tag = tag_mapping.get(tag_detail_cleaned, tag_detail_cleaned)
                        
                        try:
                            timestamp_obj = pd.to_datetime(timestamp_str, format='%Y-%m-%d_%H.%M.%S.%f', errors='coerce')
                            if pd.notna(timestamp_obj):
                                logging.debug(f"  -> SUCCESS: Parsed: Crane={crane_number}, Tag='{human_readable_tag}', Value='{result_str.strip()}'")
                                database.insert_stat(
                                    timestamp=timestamp_obj,
                                    crane_number=crane_number,
                                    tag_name=human_readable_tag,
                                    result=result_str.strip()
                                )
                            else:
                                logging.warning(f"  -> FAILED: Could not parse timestamp '{timestamp_str}'")
                        except Exception as e:
                            logging.error(f"  -> FAILED: DB insert error: {e} | Line: {line.strip()}")
                    else:
                        logging.warning(f"  -> FAILED: Could not extract tag detail from: {full_tag_string}")
                else:
                    logging.warning(f"  -> FAILED: Could not extract crane number from: {full_tag_string}")
            else:
                logging.warning(f"  -> FAILED: Regex did not match the line structure.")

    # --- File Reading Logic ---
    if file_extension == '.zip':
        logging.info(f"Processing ZIP: '{os.path.basename(current_file_path)}'")
        try:
            with zipfile.ZipFile(current_file_path, 'r') as zf:
                for log_file_name in [name for name in zf.namelist() if name.lower().endswith('.log')]:
                    logging.debug(f"  Processing inner file: {log_file_name}")
                    with zf.open(log_file_name, 'r') as infile:
                        for i, line_bytes in enumerate(infile):
                            try:
                                line = line_bytes.decode('utf-8', errors='ignore')
                                process_line(line, i + 1)
                            except Exception as e:
                                logging.error(f"Error decoding line {i+1} in {log_file_name}: {e}")
        except zipfile.BadZipFile:
            logging.error(f"Error: Bad zip file '{current_file_path}'. Skipping.")

    elif file_extension == '.log':
        logging.info(f"Processing LOG: '{os.path.basename(current_file_path)}'")
        with open(current_file_path, 'r', encoding='utf-8', errors='ignore') as infile:
            for i, line in enumerate(infile):
                process_line(line, i + 1)

# --- Final Summary ---
end_time = time.time()
execution_time = end_time - start_time
logging.info(f"--- Script execution completed in {execution_time:.2f} seconds. ---")
logging.info("Database rebuild process is complete.")
