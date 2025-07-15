from azure.identity import DefaultAzureCredential
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import *
import os

# Configuration
subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
resource_group = "your-resource-group"
data_factory_name = "your-data-factory"
location = "eastus"

# SQL Configuration
sql_server = "your-sql-server"
sql_database = "your-database"

linked_service_sql = "AzureSqlDatabaseLinkedService"

# Dataset Names
dataset_sql_products = "ProductsSQLDataset"
dataset_sql_customers = "CustomersSQLDataset"
dataset_json_sink = "JSONSinkDataset"

def create_foreach_pipeline():
    try:
        credential = DefaultAzureCredential()
        adf_client = DataFactoryManagementClient(credential, subscription_id)

        # 1. Create SQL linked service if it doesn't exist
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
        # Products dataset with filter
        products_dataset = DatasetResource(
            properties=AzureSqlTableDataset(
                linked_service_name=linked_service_sql,
                table_name="dbo.Products",
                parameters={
                    "ProductIdFilter": {
                        "type": "int",
                        "defaultValue": 100
                    }
                }
            )
        )
        adf_client.datasets.create_or_update(
            resource_group, data_factory_name, dataset_sql_products, products_dataset)

        # Customers dataset with filter
        customers_dataset = DatasetResource(
            properties=AzureSqlTableDataset(
                linked_service_name=linked_service_sql,
                table_name="dbo.Customers",
                parameters={
                    "CustomerIdMin": {
                        "type": "int",
                        "defaultValue": 100
                    },
                    "CustomerIdMax": {
                        "type": "int",
                        "defaultValue": 1000
                    }
                }
            )
        )
        adf_client.datasets.create_or_update(
            resource_group, data_factory_name, dataset_sql_customers, customers_dataset)

        # JSON sink dataset
        json_sink = DatasetResource(
            properties=JsonDataset(
                linked_service_name=LinkedServiceReference(reference_name=linked_service_sql),
                location=AzureBlobStorageLocation(
                    folder_path="output/@{formatDateTime(utcnow(),'yyyy')}/@{formatDateTime(utcnow(),'MM')}/@{formatDateTime(utcnow(),'dd')}",
                    file_name="@{item().outputFileName}.json"
                ),
                encoding_name="UTF-8"
            )
        )
        adf_client.datasets.create_or_update(
            resource_group, data_factory_name, dataset_json_sink, json_sink)

        # 3. Define the copy activities configuration
        product_copy = {
            "name": "CopyProductsData",
            "type": "Copy",
            "inputs": [
                {
                    "referenceName": dataset_sql_products,
                    "type": "DatasetReference",
                    "parameters": {
                        "ProductIdFilter": 100
                    }
                }
            ],
            "outputs": [
                {
                    "referenceName": dataset_json_sink,
                    "type": "DatasetReference",
                    "parameters": {
                        "outputFileName": "products_filtered"
                    }
                }
            ],
            "typeProperties": {
                "source": {
                    "type": "AzureSqlSource",
                    "sqlReaderQuery": "SELECT * FROM dbo.Products WHERE ProductID > @{dataset().ProductIdFilter}"
                },
                "sink": {
                    "type": "JsonSink"
                }
            }
        }

        customer_copy = {
            "name": "CopyCustomersData",
            "type": "Copy",
            "inputs": [
                {
                    "referenceName": dataset_sql_customers,
                    "type": "DatasetReference",
                    "parameters": {
                        "CustomerIdMin": 100,
                        "CustomerIdMax": 1000
                    }
                }
            ],
            "outputs": [
                {
                    "referenceName": dataset_json_sink,
                    "type": "DatasetReference",
                    "parameters": {
                        "outputFileName": "customers_filtered"
                    }
                }
            ],
            "typeProperties": {
                "source": {
                    "type": "AzureSqlSource",
                    "sqlReaderQuery": "SELECT * FROM dbo.Customers WHERE CustomerID > @{dataset().CustomerIdMin} AND CustomerID < @{dataset().CustomerIdMax}"
                },
                "sink": {
                    "type": "JsonSink"
                }
            }
        }

        # 4. Create ForEach activity with both copy activities
        for_each_activity = ForEachActivity(
            name="ForEachTableCopy",
            items=JsonPath.read("$.Pipeline.parameters.TablesToCopy"),
            activities=[product_copy, customer_copy]
        )

        # 5. Create the pipeline
        pipeline = PipelineResource(
            activities=[for_each_activity],
            parameters={
                "TablesToCopy": {
                    "type": "Array",
                    "defaultValue": ["products", "customers"]
                }
            }
        )

        # Deploy the pipeline
        pipeline = adf_client.pipelines.create_or_update(
            resource_group_name=resource_group,
            factory_name=data_factory_name,
            pipeline_name="Foreach_Example2",
            pipeline=pipeline
        )

        print(f"Pipeline 'Foreach_Example2' created successfully!")

    except Exception as e:
        print(f"Error creating pipeline: {str(e)}")

if __name__ == "__main__":
    create_foreach_pipeline()
