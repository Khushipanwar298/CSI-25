from azure.identity import DefaultAzureCredential
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import *
from datetime import datetime
import os

# Configuration
subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
resource_group = "your-resource-group"
data_factory_name = "your-data-factory"
location = "eastus" 

# ADLS Gen2 configuration
adls_account = "yourdatalake"
linked_service_adls = "AzureDataLakeStorageLinkedService"
dataset_threshold = "ThresholdDataset"
dataset_customer_sql = "CustomerSQLDataset"
dataset_customer_json = "CustomerJSONDataset"

# SQL Server configuration
sql_server = "your-sql-server"
sql_database = "your-database"
linked_service_sql = "AzureSqlDatabaseLinkedService"

# Authenticate
credential = DefaultAzureCredential()
adf_client = DataFactoryManagementClient(credential, subscription_id)

def create_data_factory_pipeline():
    try:
        # 1. Create linked services (if they don't exist)
        # ADLS Gen2 linked service
        adls_connection_string = f"DefaultEndpointsProtocol=https;AccountName={adls_account};EndpointSuffix=core.windows.net"
        self_hosted_integration_runtime = "AutoResolveIntegrationRuntime"

        adls_linked_service = LinkedServiceResource(
            properties=AzureBlobStorageLinkedService(
                connection_string=adls_connection_string
            )
        )
        adf_client.linked_services.create_or_update(
            resource_group_name=resource_group,
            factory_name=data_factory_name,
            linked_service_name=linked_service_adls,
            linked_service=adls_linked_service
        )

        # SQL DB linked service
        sql_connection_string = (
            f"Server=tcp:{sql_server}.database.windows.net,1433;"
            f"Database={sql_database};User ID=your-user;Password=your-password;"
            "Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"
        )
        sql_linked_service = LinkedServiceResource(
            properties=AzureSqlDatabaseLinkedService(
                connection_string=sql_connection_string
            )
        )
        adf_client.linked_services.create_or_update(
            resource_group_name=resource_group,
            factory_name=data_factory_name,
            linked_service_name=linked_service_sql,
            linked_service=sql_linked_service
        )

        # 2. Create datasets
        # ADLS threshold file dataset
        threshold_dataset = DatasetResource(
            properties=JsonDataset(
                linked_service_name=linked_service_adls,
                location=AzureBlobStorageLocation(
                    folder_path="path/to/thresholds",
                    file_name="/threshold_value.json"
                ),
                encoding_name="UTF-8"
            )
        )
        adf_client.datasets.create_or_update(
            resource_group, data_factory_name, dataset_threshold, threshold_dataset)

        # SQL customer table dataset
        sql_dataset = DatasetResource(
            properties=AzureSqlTableDataset(
                linked_service_name=linked_service_sql,
                table_name="dbo.CustomerTable"
            )
        )
        adf_client.datasets.create_or_update(
            resource_group, data_factory_name, dataset_customer_sql, sql_dataset)

        # JSON sink dataset with dynamic folder path
        json_dataset = DatasetResource(
            properties=JsonDataset(
                linked_service_name=linked_service_adls,
                location=AzureBlobStorageLocation(
                    folder_path=f"Customer/@{format_time('yyyy')}/@{format_time('MM')}/@{format_time('dd')}",
                    file_name="customer_data_@{format_time('yyyyMMdd_HHmmss')}.json"
                ),
            )
        )
        adf_client.datasets.create_or_update(
            resource_group, data_factory_name, dataset_customer_json, json_dataset)

        # 3. Create pipeline with activities
        # GetThreshold activity
        get_threshold = GetMetadataActivity(
            name="GetThreshold",
            dataset=DatasetReference(reference_name=dataset_threshold),
            field_list=["childItems"]
        )

        # GetRecordCount activity
        get_record_count = LookupActivity(
            name="GetRecordCount",
            source=AzureSqlSource(
                sql_reader_query="SELECT COUNT(*) AS RecordCount FROM dbo.CustomerTable"
            ),
            dataset=DatasetReference(reference_name=dataset_customer_sql)
        )

        # If Condition activity setup
        threshold_expression = (
            "@greater(activity('GetRecordCount').output.firstRow.RecordCount, "
            "activity('GetThreshold').output.childItems[0].threshold)"
        )

        # Copy activity
        copy_activity = CopyActivity(
            name="CopyCustomerData",
            source=AzureSqlSource(
                sql_reader_query="SELECT * FROM dbo.CustomerTable"
            ),
            sink=JsonSink(
                store_settings=AzureBlobStorageWriteSettings()
            ),
            inputs=[DatasetReference(reference_name=dataset_customer_sql)],
            outputs=[DatasetReference(reference_name=dataset_customer_json)]
        )

        # If condition
        if_condition_activity = IfConditionActivity(
            name="CheckThreshold",
            expression=Expression(
                value=threshold_expression
            ),
            if_true_activities=[copy_activity]
        )

        # Create pipeline with all activities
        pipeline = PipelineResource(
            activities=[get_threshold, get_record_count, if_condition_activity]
        )

        # Deploy the pipeline
        pipeline = adf_client.pipelines.create_or_update(
            resource_group_name=resource_group,
            factory_name=data_factory_name,
            pipeline_name="CustomerDataExportPipeline",
            pipeline=pipeline
        )

        print(f"Pipeline created successfully: {pipeline.name}")

    except Exception as e:
        print(f"Error creating pipeline: {str(e)}")

# Helper function for time formatting in expressions
def format_time(format_str):
    return f"{{{{formatDateTime('{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}','{format_str}')}}}}"

if __name__ == "__main__":
    create_data_factory_pipeline()
