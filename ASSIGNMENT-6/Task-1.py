import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import (
    LinkedServiceResource,
    IntegrationRuntimeReference,
    DatasetResource,
    PipelineResource,
    CopyActivity,
    SqlServerLinkedService,
    AzureSqlDatabaseLinkedService,
    SqlServerTableDataset,
    AzureSqlTableDataset,
    DatasetReference,
    PipelineReference,
    ActivityDependency,
    DatasetCompression,
    DatasetSchema,
    DatasetStorageFormat,
    CopySource,
    CopySink,
    SqlSource,
    SqlSink,
    IntegrationRuntimeOutboundNetworkDependenciesEndpointsResponse
)

# --- Configuration ---
# Replace with your actual values
subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID", "YOUR_SUBSCRIPTION_ID")
resource_group_name = "your-adf-resource-group"
data_factory_name = "your-adf-name"
location = "East US"  # Or your ADF region

# On-premises SQL Server details (replace with your server info)
on_prem_sql_server_name = "YOUR_PREM_SERVER_NAME"
on_prem_sql_database_name = "YOUR_PREM_DATABASE_NAME"
on_prem_sql_username = "YOUR_PREM_SQL_USERNAME"
on_prem_sql_password = "YOUR_PREM_SQL_PASSWORD" # Consider Azure Key Vault for production
on_prem_sql_table_name = "YourSourceTable" # Table to extract

# Azure SQL Database details (replace with your Azure SQL DB info)
azure_sql_db_server_name = "your-azuresql-server.database.windows.net"
azure_sql_db_name = "YourAzureSqlDbName"
azure_sql_db_username = "your-azuresql-username"
azure_sql_db_password = "your-azuresql-password" # Consider Azure Key Vault for production
azure_sql_db_table_name = "YourTargetTable" # Table to load into

# SHIR name (this should match the name of your already registered SHIR in ADF)
self_hosted_ir_name = "YourSelfHostedIR"

# --- Azure Authentication ---
# For local development, DefaultAzureCredential will try various methods
# including environment variables (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID)
# or Azure CLI login. For production, consider Managed Identity.
credential = DefaultAzureCredential()

# --- Data Factory Management Client ---
adf_client = DataFactoryManagementClient(credential, subscription_id)

print(f"Connecting to Azure Data Factory: {data_factory_name} in {resource_group_name}")

try:
    # 1. Create Linked Service for On-Premises SQL Server (using SHIR)
    print("Creating On-Premises SQL Server Linked Service...")
    on_prem_sql_linked_service_name = "LS_OnPremSqlServer"
    on_prem_sql_linked_service = SqlServerLinkedService(
        connection_string=f"Data Source={on_prem_sql_server_name};Initial Catalog={on_prem_sql_database_name};User ID={on_prem_sql_username};Password={on_prem_sql_password};",
        integration_runtime=IntegrationRuntimeReference(
            reference_name=self_hosted_ir_name,
            type="IntegrationRuntimeReference"
        ),
        # If you need encrypted credentials, use Azure Key Vault and reference it here
        # Instead of directly in connection string, you would use secretUri or secretName
        # on_prem_sql_linked_service.password = SecretBase(type="AzureKeyVaultSecret", store=LinkedServiceReference(...), secret_name="...")
    )
    adf_client.linked_services.create_or_update(
        resource_group_name, data_factory_name, on_prem_sql_linked_service_name, on_prem_sql_linked_service
    )
    print(f"Created Linked Service: {on_prem_sql_linked_service_name}")

    # 2. Create Linked Service for Azure SQL Database
    print("Creating Azure SQL Database Linked Service...")
    azure_sql_db_linked_service_name = "LS_AzureSqlDatabase"
    azure_sql_db_linked_service = AzureSqlDatabaseLinkedService(
        connection_string=f"Server=tcp:{azure_sql_db_server_name},1433;Database={azure_sql_db_name};User ID={azure_sql_db_username};Password={azure_sql_db_password};",
        # No integration_runtime needed here if your ADF is in the same region as Azure SQL DB
        # or if you use Azure IR directly.
    )
    adf_client.linked_services.create_or_update(
        resource_group_name, data_factory_name, azure_sql_db_linked_service_name, azure_sql_db_linked_service
    )
    print(f"Created Linked Service: {azure_sql_db_linked_service_name}")

    # 3. Create Dataset for On-Premises SQL Server Source
    print("Creating On-Premises SQL Server Dataset...")
    on_prem_sql_dataset_name = "DS_OnPremSourceTable"
    on_prem_sql_dataset = SqlServerTableDataset(
        linked_service_name=LinkedServiceReference(reference_name=on_prem_sql_linked_service_name),
        table_name=on_prem_sql_table_name,
        schema="dbo" # Or your schema name
    )
    adf_client.datasets.create_or_update(
        resource_group_name, data_factory_name, on_prem_sql_dataset_name, on_prem_sql_dataset
    )
    print(f"Created Dataset: {on_prem_sql_dataset_name}")

    # 4. Create Dataset for Azure SQL Database Sink
    print("Creating Azure SQL Database Dataset...")
    azure_sql_db_dataset_name = "DS_AzureSqlTargetTable"
    azure_sql_db_dataset = AzureSqlTableDataset(
        linked_service_name=LinkedServiceReference(reference_name=azure_sql_db_linked_service_name),
        table_name=azure_sql_db_table_name,
        schema="dbo" # Or your schema name
    )
    adf_client.datasets.create_or_update(
        resource_group_name, data_factory_name, azure_sql_db_dataset_name, azure_sql_db_dataset
    )
    print(f"Created Dataset: {azure_sql_db_dataset_name}")

    # 5. Create Pipeline with Copy Data Activity
    print("Creating Pipeline with Copy Data activity...")
    pipeline_name = "Pipeline_OnPremToAzureSql"
    copy_activity = CopyActivity(
        name="CopyDataFromOnPremToAzureSql",
        inputs=[DatasetReference(reference_name=on_prem_sql_dataset_name)],
        outputs=[DatasetReference(reference_name=azure_sql_db_dataset_name)],
        source=SqlSource(sql_reader_query=f"SELECT * FROM {on_prem_sql_table_name}"), # Or your specific query
        sink=SqlSink(write_behavior="Insert", table_option="autoCreate") # autoCreate will create table if not exists
    )
    pipeline = PipelineResource(
        activities=[copy_activity]
    )
    adf_client.pipelines.create_or_update(
        resource_group_name, data_factory_name, pipeline_name, pipeline
    )
    print(f"Created Pipeline: {pipeline_name}")

    print("\nADF resources successfully created/updated.")
    print(f"You can now go to Azure Data Factory Studio and trigger the pipeline '{pipeline_name}'.")

except Exception as e:
    print(f"An error occurred: {e}")