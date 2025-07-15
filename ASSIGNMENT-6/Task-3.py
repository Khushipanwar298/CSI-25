import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from azure.identity import DefaultAzureCredential
from azure.mgmt.datafactory import DataFactoryManagementClient
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('incremental_pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class IncrementalDataPipeline:
    def __init__(self, config):
        """Initialize the incremental loader with configuration"""
        self.config = config
        self.azure_credential = DefaultAzureCredential()
        self.source_engine = create_engine(config['source']['connection_string'])
        self.target_engine = create_engine(config['target']['connection_string'])
        
        # Initialize ADF client if using ADF orchestration
        if config.get('adf'):
            self.adf_client = DataFactoryManagementClient(
                self.azure_credential,
                config['adf']['subscription_id']
            )
    
    def get_last_watermark(self, table_name):
        """Retrieve the last watermark value from control table"""
        with self.target_engine.connect() as conn:
            result = conn.execute(
                text("SELECT last_watermark FROM etl_watermarks WHERE table_name = :table_name"),
                {'table_name': table_name}
            ).fetchone()
            
            return result[0] if result else self.config['default_watermark']
    
    def update_watermark(self, table_name, new_watermark):
        """Update the watermark in control table"""
        with self.target_engine.connect() as conn:
            conn.execute(
                text("""
                MERGE INTO etl_watermarks AS target
                USING (SELECT :table_name AS table_name, :new_watermark AS new_watermark) AS source
                ON target.table_name = source.table_name
                WHEN MATCHED THEN
                    UPDATE SET last_watermark = source.new_watermark, updated_at = GETDATE()
                WHEN NOT MATCHED THEN
                    INSERT (table_name, last_watermark, created_at, updated_at)
                    VALUES (source.table_name, source.new_watermark, GETDATE(), GETDATE());
                """),
                {'table_name': table_name, 'new_watermark': new_watermark}
            )
            conn.commit()
    
    def extract_incremental_data(self, table_name, watermark_column):
        """Extract data changed since last watermark"""
        last_watermark = self.get_last_watermark(table_name)
        logging.info(f"Last watermark for {table_name}: {last_watermark}")
        
        query = f"""
        SELECT * 
        FROM {table_name} 
        WHERE {watermark_column} > :watermark
        ORDER BY {watermark_column}
        """
        
        with self.source_engine.connect() as conn:
            df = pd.read_sql(
                text(query),
                conn,
                params={'watermark': last_watermark}
            )
        
        return df
    
    def load_data(self, df, target_table):
        """Load data to target destination"""
        if df.empty:
            logging.info("No new records to process")
            return
        
        logging.info(f"Loading {len(df)} records to {target_table}")
        
        # Upsert logic - adjust based on your target database
        with self.target_engine.connect() as conn:
            df.to_sql(
                'temp_' + target_table,
                conn,
                if_exists='replace',
                index=False
            )
            
            # Example of merge/upsert for SQL Server
            conn.execute(text(f"""
            MERGE INTO {target_table} AS target
            USING temp_{target_table} AS source
            ON target.id = source.id
            WHEN MATCHED THEN
                UPDATE SET {', '.join(f"{col} = source.{col}" for col in df.columns if col != 'id')}
            WHEN NOT MATCHED THEN
                INSERT ({', '.join(df.columns)})
                VALUES ({', '.join(f'source.{col}' for col in df.columns)});
            
            DROP TABLE temp_{target_table};
            """))
            conn.commit()
    
    def run_pipeline(self):
        """Execute the complete incremental load process"""
        try:
            for job in self.config['jobs']:
                table_name = job['source_table']
                watermark_column = job['watermark_column']
                target_table = job.get('target_table', table_name)
                
                logging.info(f"Starting incremental load for {table_name}")
                
                # Extract new/changed data
                new_data = self.extract_incremental_data(table_name, watermark_column)
                
                # Transform data if needed (add your transforms here)
                processed_data = self.transform_data(new_data, job.get('transformations'))
                
                # Load to target
                self.load_data(processed_data, target_table)
                
                # Update watermark if successful
                if not new_data.empty:
                    new_watermark = new_data[watermark_column].max()
                    self.update_watermark(table_name, new_watermark)
                    logging.info(f"Updated watermark for {table_name} to {new_watermark}")
                
                logging.info(f"Completed incremental load for {table_name}")
        
        except Exception as e:
            logging.error(f"Pipeline failed: {str(e)}")
            raise
    
    def transform_data(self, data, transformations):
        """Apply transformations to the data"""
        if not transformations or data.empty:
            return data
        
        # Example transformation - add your specific transformations
        df = data.copy()
        
        if 'column_mapping' in transformations:
            for old_name, new_name in transformations['column_mapping'].items():
                if old_name in df.columns:
                    df.rename(columns={old_name: new_name}, inplace=True)
        
        if 'data_type_conversions' in transformations:
            for col, dtype in transformations['data_type_conversions'].items():
                if col in df.columns:
                    df[col] = df[col].astype(dtype)
        
        return df
    
    def trigger_adf_pipeline(self, pipeline_name, parameters=None):
        """Trigger ADF pipeline if configured"""
        if not hasattr(self, 'adf_client'):
            logging.warning("ADF client not configured - skipping orchestration")
            return
        
        logging.info(f"Triggering ADF pipeline: {pipeline_name}")
        
        resource_group = self.config['adf']['resource_group']
        factory_name = self.config['adf']['factory_name']
        
        run_response = self.adf_client.pipelines.create_run(
            resource_group,
            factory_name,
            pipeline_name,
            parameters=parameters or {}
        )
        
        return run_response.run_id

# Example configuration
config = {
    'source': {
        'connection_string': 'mssql+pyodbc://user:password@server/database?driver=ODBC+Driver+17+for+SQL+Server'
    },
    'target': {
        'connection_string': 'mssql+pyodbc://user:password@server/database?driver=ODBC+Driver+17+for+SQL+Server'
    },
    'default_watermark': '1900-01-01 00:00:00',
    'jobs': [
        {
            'source_table': 'orders',
            'target_table': 'dim_orders',
            'watermark_column': 'last_updated',
            'transformations': {
                'column_mapping': {'order_id': 'id', 'order_date': 'date'},
                'data_type_conversions': {'amount': 'float'}
            }
        },
        {
            'source_table': 'customers',
            'watermark_column': 'modified_at',
            'transformations': {}
        }
    ],
    'adf': {
        'subscription_id': 'your-subscription-id',
        'resource_group': 'your-resource-group',
        'factory_name': 'your-data-factory'
    }
}

def main():
    pipeline = IncrementalDataPipeline(config)
    
    # Run the Python pipeline
    pipeline.run_pipeline()
    
    # Optionally trigger ADF pipeline for orchestration
    # pipeline.trigger_adf_pipeline("master_orchestration_pipeline")

if __name__ == '__main__':
    main()
