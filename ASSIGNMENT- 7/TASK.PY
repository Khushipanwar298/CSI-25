import pandas as pd
import glob
import os
from datetime import datetime
import logging
from sqlalchemy import create_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_loader.log'),
        logging.StreamHandler()
    ]
)

def get_db_engine():
    """Create and return a SQLAlchemy engine for database connection"""
    # Replace with your database connection details
    db_url = "postgresql://root:Khushi@@123@localhost:5432/your_database"
    return create_engine(db_url)

def parse_date_from_filename(filename, pattern):
    """Extract date from filename based on naming pattern"""
    if pattern == "CUST_MSTR":
        date_str = filename.split('_')[2].split('.')[0]
    elif pattern == "master_child":
        date_str = filename.split('-')[1].split('.')[0]
    else:
        return None
    
    try:
        return datetime.strptime(date_str, "%Y%m%d").date()
    except ValueError as e:
        logging.error(f"Error parsing date from filename {filename}: {e}")
        return None

def process_cust_mstr_files(files, engine):
    """Process CUST_MSTR files and load to database"""
    for file in files:
        try:
            df = pd.read_csv(file)
            date_obj = parse_date_from_filename(os.path.basename(file), "CUST_MSTR")
            
            if date_obj:
                df['Date'] = date_obj.strftime("%Y-%m-%d")
                
                # Truncate table for daily fresh load
                with engine.begin() as connection:
                    connection.execute("TRUNCATE TABLE CUST_MSTR")
                
                # Load to database
                df.to_sql('CUST_MSTR', engine, if_exists='append', index=False)
                logging.info(f"Successfully loaded {file} to CUST_MSTR table")
            else:
                logging.warning(f"Skipped {file} due to date parsing error")
                
        except Exception as e:
            logging.error(f"Error processing {file}: {e}")

def process_master_child_files(files, engine):
    """Process master_child_export files and load to database"""
    for file in files:
        try:
            df = pd.read_csv(file)
            date_obj = parse_date_from_filename(os.path.basename(file), "master_child")
            
            if date_obj:
                df['Date'] = date_obj.strftime("%Y-%m-%d")
                df['DateKey'] = date_obj.strftime("%Y%m%d")
                
                # Truncate table for daily fresh load
                with engine.begin() as connection:
                    connection.execute("TRUNCATE TABLE master_child")
                
                # Load to database
                df.to_sql('master_child', engine, if_exists='append', index=False)
                logging.info(f"Successfully loaded {file} to master_child table")
            else:
                logging.warning(f"Skipped {file} due to date parsing error")
                
        except Exception as e:
            logging.error(f"Error processing {file}: {e}")

def process_h_ecom_files(files, engine):
    """Process H_ECOM_ORDER files and load to database"""
    for file in files:
        try:
            df = pd.read_csv(file)
            
            # Truncate table for daily fresh load
            with engine.begin() as connection:
                connection.execute("TRUNCATE TABLE H_ECOM_Orders")
            
            # Load to database
            df.to_sql('H_ECOM_Orders', engine, if_exists='append', index=False)
            logging.info(f"Successfully loaded {file} to H_ECOM_Orders table")
            
        except Exception as e:
            logging.error(f"Error processing {file}: {e}")

def main():
    """Main execution function"""
    try:
        db_engine = get_db_engine()
        
        # Find all files in the data lake
        cust_mstr_files = glob.glob('data_lake/CUST_MSTR_*.csv')
        master_child_files = glob.glob('data_lake/master_child_export-*.csv')
        h_ecom_files = glob.glob('data_lake/H_ECOM_ORDER.csv')
        
        # Process each file type
        if cust_mstr_files:
            process_cust_mstr_files(cust_mstr_files, db_engine)
        else:
            logging.warning("No CUST_MSTR files found")
            
        if master_child_files:
            process_master_child_files(master_child_files, db_engine)
        else:
            logging.warning("No master_child_export files found")
            
        if h_ecom_files:
            process_h_ecom_files(h_ecom_files, db_engine)
        else:
            logging.warning("No H_ECOM_ORDER files found")
            
    except Exception as e:
        logging.error(f"Fatal error in main execution: {e}")
    finally:
        db_engine.dispose()
        logging.info("Process completed")

if __name__ == "__main__":
    logging.info("Starting data loader process")
    main()
