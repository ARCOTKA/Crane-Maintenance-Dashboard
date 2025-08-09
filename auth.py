# SCRIPT NAME: auth.py
# DESCRIPTION: Handles user authentication by reading from an external users.json file.
# UPDATE: Simplified to only verify an admin password, without checking username.
# REFACTOR: Centralized path and logger configuration.

import json
import os
from config import Paths, logger # Import from the new centralized config

def load_users():
    """
    Reads the users.json file and returns the list of user objects.

    This function is responsible for safely loading user data from the JSON file.
    It handles cases where the file might not exist or is improperly formatted.

    Returns:
        list: A list of user dictionaries. Each dictionary should contain
              keys like "username", "password", and "role".
              Returns an empty list if the file cannot be read or is empty.
    """
    logger.debug(f"Attempting to load users from: {Paths.USERS_FILE_PATH}")
    if not os.path.exists(Paths.USERS_FILE_PATH):
        logger.error(f"users.json not found at {Paths.USERS_FILE_PATH}")
        return []
    try:
        with open(Paths.USERS_FILE_PATH, 'r') as f:
            data = json.load(f)
            # .get("users", []) is a safe way to access the list.
            # If the "users" key doesn't exist, it returns an empty list instead of crashing.
            users = data.get("users", [])
            logger.debug(f"Successfully loaded {len(users)} user(s).")
            return users
    except json.JSONDecodeError as e:
        logger.critical(f"Failed to decode users.json. It might be malformed. Error: {e}")
        return []
    except Exception as e:
        logger.critical(f"An unexpected error occurred while loading users: {e}")
        return []

def verify_admin_password(password: str) -> str | None:
    """
    Checks if the provided password matches any user with the 'admin' role.

    It iterates through all users loaded from the JSON file and checks two conditions:
    1. The user's role is "admin".
    2. The user's password matches the one provided.

    Args:
        password (str): The password to check.

    Returns:
        str: The username of the matching admin if found.
        None: If no matching admin user is found.
    """
    logger.info("Verifying admin password.")
    all_users = load_users()
    for user in all_users:
        # Check if the user has the 'admin' role and the password matches.
        # .get() is used for safe access in case a key is missing from a user entry.
        if user.get("role") == "admin" and user.get("password") == password:
            username = user.get("username")
            logger.info(f"Password verification successful for admin user: '{username}'")
            return username # Return the admin's username on success
    
    logger.warning("Admin password verification failed. No matching user found.")
    return None # Return None if the loop finishes without finding a match
