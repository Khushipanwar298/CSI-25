from azure.identity import DefaultAzureCredential
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import *
import os
from azure.identity import DefaultAzureCredential
credential = DefaultAzureCredential()
print("Using DefaultAzureCredential")
#Configuration
subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
print(f"Subscription ID: {subscription_id}")  
   
resource_group = "MyResourcegroup0816"
data_factory_name = "mydatafactory1564"
location = "eastus"

# Storage and SQL Config
adls_account = "yourdatalake"
sql_server = "your-sql-server" 
sql_database = "Khushi"

# Linked Services
linked_service_sql = "AzureSqlDatabaseLinkedService"
linked_service_adls = "AzureDataLakeStorageLinkedService"

# Datasets
dataset_sql_customers = "CustomerSQLDataset"
dataset_csv_address = "CustomerAddressCSVDataset"
dataset_parquet_sink = "CustomerJoinedParquetDataset"

def create_customer_pipeline():
    try:
        credential = DefaultAzureCredential()
        adf_client = DataFactoryManagementClient(credential,subscription_id )
        
        # 1. Create Linked Services
        # SQL Linked Service
        sql_linked_service = LinkedServiceResource(
            properties=AzureSqlDatabaseLinkedService(
                connection_string=(
                    f"Server=tcp:{sql_server}.database.windows.net,1433;"
                    f"Database={sql_database};User ID=your-user;Password=your-password;"
                    "Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"
                )
            )
        )
        adf_client.linked_services.create_or_update(
            resource_group, data_factory_name, linked_service_sql, sql_linked_service)
        
        # ADLS Linked Service
        adls_linked_service = LinkedServiceResource(
            properties=AzureBlobStorageLinkedService(
                connection_string=f"DefaultEndpointsProtocol=https;AccountName={adls_account};EndpointSuffix=core.windows.net"
            )
        )
        adf_client.linked_services.create_or_update(
            resource_group, data_factory_name, linked_service_adls, adls_linked_service)

        # 2. Create Datasets
        # SQL Customer Dataset with parameter for filtering
        sql_dataset = DatasetResource(
            properties=AzureSqlTableDataset(
                linked_service_name=linked_service_sql,
                table_name="dbo.Customers",
                parameters={
                    "CustomerIdMin": {"type": "int", "defaultValue": 1000},
                    "CustomerIdMax": {"type": "int", "defaultValue": 2000}
                }
            )
        )
        adf_client.datasets.create_or_update(
            resource_group, data_factory_name, dataset_sql_customers, sql_dataset)

        # CSV Address Dataset
        csv_dataset = DatasetResource(
            properties=DelimitedTextDataset(
                linked_service_name=linked_service_adls,
                location=AzureBlobStorageLocation(
                    folder_path="customer_address_source",
                    file_name="customer_addresses.csv"
                ),
                first_row_as_header=True,
                column_delimiter=","
            )
        )
        adf_client.datasets.create_or_update(
            resource_group, data_factory_name, dataset_csv_address, csv_dataset)

        # Parquet Sink Dataset with dynamic path
        parquet_dataset = DatasetResource(
            properties=ParquetDataset(
                linked_service_name=linked_service_adls,
                location=AzureBlobStorageLocation(
                    folder_path="joined_customer_data/year=@{formatDateTime(utcnow(),'yyyy')}/month=@{formatDateTime(utcnow(),'MM')}/day=@{formatDateTime(utcnow(),'dd')}",
                    file_name="customers_1000_2000.parquet"
                )
            )
        )
        adf_client.datasets.create_or_update(
            resource_group, data_factory_name, dataset_parquet_sink, parquet_dataset)

        # 3. Create Data Flow for Join and Transformation
        data_flow = DataFlowResource(
            properties=MappingDataFlow(
                description="Join customer data with addresses and filter",
                sources=[
                    DataFlowSource(
                        name="CustomerSQLSource",
                        dataset=DatasetReference(reference_name=dataset_sql_customers),
                        sqlReaderQuery="SELECT * FROM dbo.Customers WHERE CustomerID > 1000 AND CustomerID < 2000 ORDER BY CustomerID ASC"
                    ),
                    DataFlowSource(
                        name="AddressCSVSource",
                        dataset=DatasetReference(reference_name=dataset_csv_address)
                    )
                ],
                sinks=[
                    DataFlowSink(
                        name="JoinedSink",
                        dataset=DatasetReference(reference_name=dataset_parquet_sink),
                        schema_linked_service=LinkedServiceReference(reference_name=linked_service_adls)
                    )
                ],
                transformations=[
                    DataFlowTransformation(
                        name="JoinCustomersWithAddresses",
                        type="Join",
                        inputs=[
                            DataFlowReference(reference_name="CustomerSQLSource"),
                            DataFlowReference(reference_name="AddressCSVSource")
                        ],
                        joinType="Inner",
                        joinConditions=[
                            DataFlowExpressionPair(
                                left="CustomerSQLSource.CustomerID",
                                right="AddressCSVSource.CustomerID"
                            )
                        ]
                    ),
                    DataFlowTransformation(
                        name="FilterAndSort",
                        type="Select",
                        inputs=[DataFlowReference(reference_name="JoinCustomersWithAddresses")],
                        columns=[
                            "CustomerSQLSource.CustomerID as CustomerID", 
                            "CustomerSQLSource.*",
                            "AddressCSVSource.* except(CustomerID)"
                        ]
                    )
                ]
            )
        )
        adf_client.data_flows.create_or_update(
            resource_group, data_factory_name, "CustomerJoinDataFlow", data_flow)

        # 4. Create Pipeline with Data Flow Activity
        pipeline = PipelineResource(
            activities=[
                ExecuteDataFlowActivity(
                    name="ExecuteCustomerJoin",
                    dataFlow=DataFlowReference(
                        reference_name="CustomerJoinDataFlow",
                        type="DataFlowReference"
                    )
                )
            ]
        )

        adf_client.pipelines.create_or_update(
            resource_group, data_factory_name, "CustomerJoinPipeline", pipeline)

        print("Pipeline created successfully to join customer data and save as Parquet!")

    except Exception as e:
        print(f"Error creating pipeline: {str(e)}")

if __name__ == "__main__":
    create_customer_pipeline()
