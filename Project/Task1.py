import os
import pandas as pd
from sqlalchemy import create_engine
import json
import argparse
import logging
from azure.storage.filedatalake import DataLakeServiceClient
from azure.identity import DefaultAzureCredential # Recommended for Azure authentication

# --- Configuration ---
# Set up logging for better visibility into pipeline operations
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONFIG = {
    
    "sql_connection": os.getenv("SQL_CONNECTION_STRING", "mssql+pyodbc://<root>:<Khushi@@123>@<server_name>/<khushi>?driver=ODBC+Driver+18+for+SQL+Server"),
    

    "threshold_file_name": "threshold.txt", # Only the filename
    "output_json_file_name": "customers.json", # Only the filename
    "local_data_dir": "./pipeline_data", # Directory for local files

    
    "adls_account_name": os.getenv("ADLS_ACCOUNT_NAME", "your_adls_account_name"),
    "adls_file_system_name": os.getenv("ADLS_FILE_SYSTEM_NAME", "your_file_system_name"),
    "adls_directory_name": os.getenv("ADLS_DIRECTORY_NAME", "your_directory_name"),
    
    "default_threshold": 1000  # Default threshold value
}

# Construct full local paths
CONFIG["threshold_path"] = os.path.join(CONFIG["local_data_dir"], CONFIG["threshold_file_name"])
CONFIG["output_path"] = os.path.join(CONFIG["local_data_dir"], CONFIG["output_json_file_name"])


# --- Helper Functions ---
def setup_directories():
    """Create required local directories if they don't exist."""
    try:
        os.makedirs(CONFIG["local_data_dir"], exist_ok=True)
        logging.info(f"Local data directory '{CONFIG['local_data_dir']}' ensured.")
    except Exception as e:
        logging.error(f"Error creating local data directory: {e}")
        raise # Re-raise to stop execution if directories can't be created

def create_threshold_file_local():
    """Create the threshold file locally with the default value."""
    try:
        setup_directories() # Ensure parent directory exists
        with open(CONFIG["threshold_path"], 'w') as f:
            f.write(str(CONFIG["default_threshold"]))
        logging.info(f"Local threshold file created at '{CONFIG['threshold_path']}' with value {CONFIG['default_threshold']}.")
    except Exception as e:
        logging.error(f"Error creating local threshold file: {e}")
        raise

def read_threshold():
    """Read the threshold value from the local file."""
    try:
        with open(CONFIG["threshold_path"], 'r') as f:
            threshold_value = int(f.read().strip())
        logging.info(f"Threshold value '{threshold_value}' read from '{CONFIG['threshold_path']}'.")
        return threshold_value
    except FileNotFoundError:
        logging.error(f"Threshold file not found at '{CONFIG['threshold_path']}'. Please run with --create-threshold first.")
        raise
    except ValueError:
        logging.error(f"Invalid threshold value in file '{CONFIG['threshold_path']}'. Must be an integer.")
        raise
    except Exception as e:
        logging.error(f"Error reading threshold from file: {e}")
        raise

def check_customer_count(engine):
    """Get the count of records in the customer table."""
    logging.info("Checking customer record count...")
    try:
        count = pd.read_sql("SELECT COUNT(*) FROM Customers", engine).iloc[0, 0]
        logging.info(f"Customer record count: {count}")
        return count
    except Exception as e:
        logging.error(f"Error getting customer count: {e}")
        raise

def get_adls_service_client():
    try:
        credential = DefaultAzureCredential()
        account_url = f"https://{CONFIG['adls_account_name']}.dfs.core.windows.net"
        service_client = DataLakeServiceClient(account_url=account_url, credential=credential)
        logging.info("Successfully obtained ADLS service client.")
        return service_client
    except Exception as e:
        logging.error(f"Error authenticating with ADLS or creating service client: {e}")
        logging.error("Ensure ADLS_ACCOUNT_NAME is correct and Azure credentials (e.g., AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID, or Azure CLI login) are configured.")
        raise

def upload_file_to_adls(local_file_path, adls_file_system_name, adls_directory_name, adls_file_name):
    """Upload a local file to Azure Data Lake Storage Gen2."""
    logging.info(f"Attempting to upload '{local_file_path}' to ADLS: {adls_file_system_name}/{adls_directory_name}/{adls_file_name}")
    try:
        service_client = get_adls_service_client()
        file_system_client = service_client.get_file_system_client(file_system=adls_file_system_name)
        
        # Ensure the file system exists (optional, depends on your setup)
        # try:
        #     file_system_client.get_file_system_properties()
        # except Exception:
        #     logging.warning(f"File system '{adls_file_system_name}' not found, attempting to create.")
        #     file_system_client.create_file_system()

        directory_client = file_system_client.get_directory_client(adls_directory_name)
        directory_client.create_directory(overwrite=True) # Ensure directory exists

        file_client = directory_client.get_file_client(adls_file_name)
        
        with open(local_file_path, "rb") as data:
            file_client.upload_data(data, overwrite=True)
        
        logging.info(f"Successfully uploaded '{os.path.basename(local_file_path)}' to ADLS: '{adls_file_system_name}/{adls_directory_name}/{adls_file_name}'.")
    except Exception as e:
        logging.error(f"Error uploading '{local_file_path}' to ADLS: {e}")
        raise

def export_customer_data(engine):
    
    logging.info("Exporting customer data...")
    try:
        customers = pd.read_sql("SELECT * FROM Customers", engine)
        
        # Convert to JSON with proper formatting
        json_data = customers.to_json(orient='records', date_format='iso', indent=2)
        
        # Save to local file
        with open(CONFIG["output_path"], 'w') as f:
            f.write(json_data)
        
        logging.info(f"Customer data exported locally to '{CONFIG['output_path']}'. Records: {len(customers)}.")
        
        # Upload to ADLS
        upload_file_to_adls(
            CONFIG["output_path"],
            CONFIG["adls_file_system_name"],
            CONFIG["adls_directory_name"],
            CONFIG["output_json_file_name"]
        )
    except Exception as e:
        logging.error(f"Error in customer data export process: {e}")
        raise

def run_pipeline():
    """Main pipeline execution for threshold-based customer data transfer."""
    logging.info("Starting data pipeline execution...")
    
    # Create SQL engine
    engine = None
    try:
        engine = create_engine(CONFIG["sql_connection"])
        logging.info("SQL database engine created successfully.")
    except Exception as e:
        logging.error(f"Error creating SQL database engine: {e}")
        return False # Pipeline cannot proceed without DB connection

    try:
        # Get threshold and customer count
        threshold = read_threshold()
        customer_count = check_customer_count(engine)
        
        logging.info(f"Comparison: Customer Count ({customer_count}) vs. Threshold ({threshold})")
        
        # Check if we need to export
        if customer_count > threshold:
            logging.info("Threshold exceeded - proceeding to export customer data.")
            export_customer_data(engine)
            logging.info("Customer data export and upload completed.")
        else:
            logging.info("Threshold not exceeded - no customer data export action taken.")
            
        return True
    except Exception as e:
        logging.error(f"Pipeline failed during execution: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Customer Data Export Pipeline based on Threshold",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--create-threshold",
        action="store_true",
        help="Create the local threshold file with default value and upload it to ADLS"
    )
    args = parser.parse_args()
    
    # Ensure local data directory exists before any file operations
    setup_directories()

    if args.create_threshold:
        create_threshold_file_local()
        try:
            # Upload the newly created local threshold file to ADLS
            upload_file_to_adls(
                CONFIG["threshold_path"],
                CONFIG["adls_file_system_name"],
                CONFIG["adls_directory_name"],
                CONFIG["threshold_file_name"]
            )
            logging.info("Threshold file successfully uploaded to ADLS.")
        except Exception as e:
            logging.error(f"Failed to upload threshold file to ADLS: {e}")
            logging.error("Please check your ADLS configuration and credentials.")
    else:
        if run_pipeline():
            logging.info("Pipeline completed successfully.")
        else:
            logging.error("Pipeline completed with errors.")
