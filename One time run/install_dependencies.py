# SCRIPT NAME: install_dependencies.py
# DESCRIPTION: A simple script to install all required libraries for the
#              Crane Maintenance Dashboard project. Run this script once.

import sys
import subprocess

# A list of all packages that need to be installed
packages = [
    "streamlit",
    "pandas",
    "fpdf",
    "openpyxl"
]

def install_packages():
    """
    Iterates through a list of packages and installs them using pip.
    """
    print("--- Starting Dependency Installation ---")
    for package in packages:
        try:
            print(f"Installing {package}...")
            # Use the same Python executable that is running this script to ensure
            # libraries are installed in the correct environment.
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Successfully installed {package}.\n")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to install {package}.")
            print(f"Please try installing it manually by running: pip install {package}")
            print(f"Error details: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            sys.exit(1)
    print("--- All dependencies are installed successfully. ---")
    print("\nYou can now run the main dashboard using the command:")
    print("python -m streamlit run dashboard.py")


if __name__ == "__main__":
    install_packages()
