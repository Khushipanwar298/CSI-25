import os

# Configuration
THRESHOLD_FILE_PATH = "./pipeline_data/threshold.txt"
DEFAULT_THRESHOLD = 1000  # Set your desired threshold value here

def create_threshold_file():
    """Create a threshold file with a default value."""
    try:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(THRESHOLD_FILE_PATH), exist_ok=True)
        
        # Write the default threshold value to the file
        with open(THRESHOLD_FILE_PATH, 'w') as f:
            f.write(str(DEFAULT_THRESHOLD))
        
        print(f"Threshold file created at: {THRESHOLD_FILE_PATH}")
    except Exception as e:
        print(f"Error creating threshold file: {str(e)}")

if __name__ == "__main__":
    create_threshold_file()
