import pandas as pd
from sqlalchemy import create_engine
import schedule
import time
import pyarrow as pa
import avro as avro
import logging
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

# --- Configuration ---
# Set up logging for better visibility into pipeline operations
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database connection strings from environment variables for security and flexibility
# Ensure these environment variables are set before running the script:
# export SOURCE_DB_CONN_STR="postgresql://root:Khushi@@123@localhost:5432/source_db"
# export TARGET_DB_CONN_STR="postgresql://root:Khushi@@123@localhost:5432/target_db"
# export EVENT_TRIGGER_DIR="./event_triggers" # Directory to monitor for event triggers

source_db_connection_string = os.getenv('SOURCE_DB_CONN_STR', 'postgresql://root:Khushi@@123@localhost:5432/source_db')
target_db_connection_string = os.getenv('TARGET_DB_CONN_STR', 'postgresql://root:Khushi@@123@localhost:5432/target_db')
event_trigger_directory = os.getenv('EVENT_TRIGGER_DIR', './event_triggers')

# Create the event trigger directory if it doesn't exist
os.makedirs(event_trigger_directory, exist_ok=True)
logging.info(f"Monitoring directory for event triggers: {event_trigger_directory}")


# --- Database Engine Creation ---
# Create database engines for source and target databases
source_engine = None
target_engine = None

try:
    source_engine = create_engine(source_db_connection_string)
    target_engine = create_engine(target_db_connection_string)
    logging.info("Database engines created successfully.")
except Exception as e:
    logging.error(f"Error creating database engines: {e}")
    # Exit if database connections cannot be established, as the pipeline cannot function
    exit(1)


# --- Data Extraction and Loading Function ---
def extract_and_load(table_name, columns=None):
    """
    Extracts data from a specified table (and optionally columns) from the source database,
    saves it to CSV, Parquet, and Avro files, and then loads it into the target database.

    Args:
        table_name (str): The name of the table to extract and load.
        columns (list, optional): A list of column names to select. If None, all columns are selected.
    """
    # Step 1: Extract data from the source database
    if columns:
        query = f"SELECT {', '.join(columns)} FROM {table_name}"
        log_columns = f" (columns: {', '.join(columns)})"
    else:
        query = f"SELECT * FROM {table_name}"
        log_columns = ""

    logging.info(f"Attempting to extract data from '{table_name}'{log_columns}...")
    try:
        data = pd.read_sql(query, source_engine)
        logging.info(f"Successfully extracted {len(data)} rows from '{table_name}'.")
    except Exception as e:
        logging.error(f"Error extracting data from '{table_name}': {e}")
        return # Stop execution if extraction fails

    # Step 2: Save to CSV
    csv_file_path = f'{table_name}.csv'
    try:
        data.to_csv(csv_file_path, index=False)
        logging.info(f"Data saved to CSV: {csv_file_path}")
    except Exception as e:
        logging.error(f"Error saving data to CSV for '{table_name}': {e}")

    # Step 3: Save to Parquet
    parquet_file_path = f'{table_name}.parquet'
    try:
        data.to_parquet(parquet_file_path, index=False)
        logging.info(f"Data saved to Parquet: {parquet_file_path}")
    except Exception as e:
        logging.error(f"Error saving data to Parquet for '{table_name}': {e}")

    # Step 4: Save to Avro
    avro_file_path = f'{table_name}.avro'
    try:
        table = pa.Table.from_pandas(data)
        with pa.OSFile(avro_file_path, 'wb') as f:
            avro.write_table(table, f)
        logging.info(f"Data saved to Avro: {avro_file_path}")
    except Exception as e:
        logging.error(f"Error saving data to Avro for '{table_name}': {e}")

    # Step 5: Load data into the target database
    # For a full replacement: if_exists='replace'
    # For appending data (consider primary key conflicts): if_exists='append'
    # For more complex upserts, custom SQL or a different library would be needed.
    try:
        data.to_sql(table_name, target_engine, if_exists='replace', index=False)
        logging.info(f"Data loaded into target database table: {table_name}")
    except Exception as e:
        logging.error(f"Error loading data into target table '{table_name}': {e}")


# --- Scheduled Pipeline Functions ---
def copy_all_tables():
    """
    Copies all tables from the source database to the target database,
    also saving them in CSV, Parquet, and Avro formats.
    This function is intended for scheduled full loads.
    """
    logging.info("Starting scheduled task: Copying all tables...")
    try:
        # Get all table names from the public schema of the source database
        tables = pd.read_sql("SELECT table_name FROM information_schema.tables WHERE table_schema='public'", source_engine)
        for table in tables['table_name']:
            extract_and_load(table)
        logging.info("Finished scheduled task: Copied all tables successfully.")
    except Exception as e:
        logging.error(f"Error retrieving table names for full copy: {e}")

def copy_specific_table(table_name, columns=None):
    """
    Initiates the extraction and loading process for a single, specific table.
    This function can be called directly or by event-based triggers.

    Args:
        table_name (str): The name of the table to copy.
        columns (list, optional): A list of column names to select.
    """
    logging.info(f"Starting specific table copy for '{table_name}'...")
    extract_and_load(table_name, columns)
    logging.info(f"Finished specific table copy for '{table_name}'.")


# --- Event-Based Trigger Setup (using watchdog) ---
class EventTriggerHandler(FileSystemEventHandler):
    """
    A custom event handler for watchdog that triggers specific table copies
    when a new file is created in the monitored directory.
    """
    def on_created(self, event):
        """
        Called when a file or directory is created.
        We check if it's a file and use its name (without extension) as the table name.
        """
        if not event.is_directory:
            file_name = os.path.basename(event.src_path)
            # Assuming file names like 'my_table.trigger' to copy 'my_table'
            if '.' in file_name:
                table_name = file_name.split('.')[0]
                logging.info(f"Event detected: New file '{file_name}' created. Triggering copy for table '{table_name}'.")
                # Run the copy in a new thread or process if it's long-running,
                # to avoid blocking the event observer. For simplicity, we call directly.
                copy_specific_table(table_name)
            else:
                logging.info(f"Ignored event: New file '{file_name}' (no recognized extension).")


# --- Pipeline Scheduling ---
# Step 6: Schedule the full pipeline to run daily at 1 AM
schedule.every().day.at("01:00").do(copy_all_tables)
logging.info("Scheduled daily full database copy at 01:00 AM.")

# Example of scheduling a specific table copy if needed (e.g., a frequently updated table)
# schedule.every(4).hours.do(copy_specific_table, 'frequently_updated_table', ['id', 'value', 'timestamp'])
# logging.info("Scheduled 'frequently_updated_table' copy every 4 hours.")

# --- Main Loop and Event Observer Start ---
if __name__ == "__main__":
    # Initialize watchdog observer for event-based triggers
    event_handler = EventTriggerHandler()
    observer = Observer()
    observer.schedule(event_handler, event_trigger_directory, recursive=False)

    # Start the observer in a separate thread to allow the main thread to run the scheduler
    logging.info(f"Starting event trigger observer for directory: {event_trigger_directory}")
    observer_thread = threading.Thread(target=observer.start)
    observer_thread.daemon = True # Allow the main program to exit even if this thread is still running
    observer_thread.start()

    logging.info("Scheduler and Event Observer started. Waiting for tasks...")

    # Step 7: Run the scheduler in an infinite loop
    while True:
        try:
            schedule.run_pending()
            time.sleep(1) # Wait for 1 second before checking again
        except KeyboardInterrupt:
            logging.info("Pipeline stopped by user (Ctrl+C).")
            observer.stop()
            observer.join()
            break
        except Exception as e:
            logging.error(f"An unexpected error occurred in the main loop: {e}")
            time.sleep(5) # Wait longer after an error to prevent rapid logging
