import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import (
    LinkedServiceResource,
    DatasetResource,
    PipelineResource,
    CopyActivity,
    SftpServerLinkedService, # For SFTP
    FtpServerLinkedService,   # For FTP
    BinaryDataset,            # For general files on FTP/SFTP
    DelimitedTextDataset,     # For CSV/TXT files
    JsonDataset,              # For JSON files
    AzureBlobStorageLinkedService, # Example destination
    AzureBlobStorageDataset,       # Example destination
    IntegrationRuntimeReference,
    LinkedServiceReference,
    DatasetReference,
    CopySource,
    CopySink,
    SftpReadSettings,
    FtpReadSettings,
    BlobSink,
    BlobSource,
    FileSystemSource, # Used by Sftp/Ftp source internally
    FileSystemSink    # Used by Blob sink internally
)

# --- Configuration ---
# Replace with your actual values
subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID", "YOUR_SUBSCRIPTION_ID")
resource_group_name = "your-adf-resource-group"
data_factory_name = "your-adf-name"
location = "East US" # Or your ADF region

# --- SFTP/FTP Server Details ---
server_host = "your-sftp-ftp-host.com" # e.g., 'sftp.partner.com' or 'ftp.yourcompany.com'
server_port = 22 # 22 for SFTP, 21 for FTP
server_username = "your-sftp-ftp-username"
server_password = "your-sftp-ftp-password" # Use Azure Key Vault for production!
# For SFTP with SSH private key, you'd use "authenticationType": "SshPublicKey",
# and provide a base64 encoded private key or reference a Key Vault secret.
# Example: ssh_private_key_path = "/path/to/your/private_key"

source_folder_path = "/data/inbound" # Path on the FTP/SFTP server
source_file_name = "*.csv" # Or 'sales_data.csv', 'data_*.txt', etc.
is_sftp = True # Set to False for FTP

# --- Destination (Example: Azure Blob Storage) ---
# Ensure you have an Azure Storage Account
storage_account_name = "yourstorageaccountname"
storage_account_key = "your_storage_account_key" # Use Azure Key Vault for production!
blob_container_name = "rawdata"
blob_output_folder = "sftp-extracted" # Folder within the container

# --- Integration Runtime Configuration ---
# IMPORTANT:
# - If your FTP/SFTP server is publicly accessible, use 'AutoResolveIntegrationRuntime'
# - If your FTP/SFTP server is behind a firewall, you MUST use a Self-Hosted IR.
#   Replace 'AutoResolveIntegrationRuntime' with your SHIR name (e.g., 'MySelfHostedIR').
integration_runtime_name = "AutoResolveIntegrationRuntime" # Default Azure IR
# integration_runtime_name = "YourSelfHostedIR" # Uncomment and replace for SHIR

# --- ADF Resource Names ---
sftp_ftp_linked_service_name = "LS_SftpFtpServer"
blob_linked_service_name = "LS_AzureBlobStorage"
sftp_ftp_dataset_name = "DS_SftpFtpSource"
blob_dataset_name = "DS_BlobSink"
pipeline_name = "Pipeline_ExtractFromSftpFtp"

# --- Azure Authentication ---
credential = DefaultAzureCredential()

# --- Data Factory Management Client ---
adf_client = DataFactoryManagementClient(credential, subscription_id)

print(f"Connecting to Azure Data Factory: {data_factory_name} in {resource_group_name}")

try:
    # 1. Create Linked Service for Azure Blob Storage (Destination)
    print("Creating Azure Blob Storage Linked Service...")
    blob_linked_service = AzureBlobStorageLinkedService(
        connection_string=f"DefaultEndpointsProtocol=https;AccountName={storage_account_name};AccountKey={storage_account_key};EndpointSuffix=core.windows.net"
    )
    adf_client.linked_services.create_or_update(
        resource_group_name, data_factory_name, blob_linked_service_name, blob_linked_service
    )
    print(f"Created Linked Service: {blob_linked_service_name}")

    # 2. Create Linked Service for FTP/SFTP Server (Source)
    print(f"Creating {'SFTP' if is_sftp else 'FTP'} Server Linked Service...")

    if is_sftp:
        # SFTP Linked Service
        sftp_ftp_linked_service_properties = SftpServerLinkedService(
            host=server_host,
            port=server_port,
            user_name=server_username,
            password={"type": "SecureString", "value": server_password}, # Securely store password
            # If using SSH private key:
            # authentication_type="SshPublicKey",
            # ssh_public_key_path="path_to_public_key_on_server_if_applicable",
            # private_key={"type": "SecureString", "value": base64_encoded_private_key_content},
            # private_key_password={"type": "SecureString", "value": "password_for_private_key"}
            # Reference a Key Vault Secret for real production scenarios:
            # password={"type": "AzureKeyVaultSecret", "store": LinkedServiceReference(reference_name="YourKeyVaultLinkedService"), "secret_name":"YourSftpPasswordSecret"}
            # ssh_private_key={"type": "AzureKeyVaultSecret", "store": LinkedServiceReference(reference_name="YourKeyVaultLinkedService"), "secret_name":"YourSftpPrivateKeySecret"}
            enable_ssh_host_key_check=False, # Set to True and provide host key for production for security
            integration_runtime=IntegrationRuntimeReference(
                reference_name=integration_runtime_name,
                type="IntegrationRuntimeReference"
            )
        )
    else:
        # FTP Linked Service
        sftp_ftp_linked_service_properties = FtpServerLinkedService(
            host=server_host,
            port=server_port,
            user_name=server_username,
            password={"type": "SecureString", "value": server_password},
            # Reference a Key Vault Secret for real production scenarios:
            # password={"type": "AzureKeyVaultSecret", "store": LinkedServiceReference(reference_name="YourKeyVaultLinkedService"), "secret_name":"YourFtpPasswordSecret"}
            enable_ssl_encryption=True, # Recommended for secure FTP
            enable_server_verification=False, # Set to True and provide server verification for production
            integration_runtime=IntegrationRuntimeReference(
                reference_name=integration_runtime_name,
                type="IntegrationRuntimeReference"
            )
        )

    adf_client.linked_services.create_or_update(
        resource_group_name, data_factory_name, sftp_ftp_linked_service_name, sftp_ftp_linked_service_properties
    )
    print(f"Created Linked Service: {sftp_ftp_linked_service_name}")


    # 3. Create Dataset for FTP/SFTP Source (e.g., DelimitedText for CSV)
    print(f"Creating {'SFTP' if is_sftp else 'FTP'} Source Dataset...")
    # Using DelimitedTextDataset for CSV files. Use BinaryDataset for any file type.
    sftp_ftp_dataset = DelimitedTextDataset(
        linked_service_name=LinkedServiceReference(reference_name=sftp_ftp_linked_service_name),
        folder_path=source_folder_path,
        file_name=source_file_name,
        # Schema and format properties for DelimitedText (adjust as per your file)
        first_row_as_header=True,
        column_delimiter=",",
        row_delimiter="\n",
        # compression=DatasetCompression(type="GZip"), # Uncomment if files are compressed
        # To specify a dynamic file path using parameters
        # parameters={"dynamicFileName": {"type": "String"}}
    )
    adf_client.datasets.create_or_update(
        resource_group_name, data_factory_name, sftp_ftp_dataset_name, sftp_ftp_dataset
    )
    print(f"Created Dataset: {sftp_ftp_dataset_name}")

    # 4. Create Dataset for Azure Blob Storage Sink
    print("Creating Azure Blob Storage Sink Dataset...")
    blob_dataset = AzureBlobStorageDataset(
        linked_service_name=LinkedServiceReference(reference_name=blob_linked_service_name),
        folder_path=blob_output_folder,
        file_name={"type": "Expression", "value": "@concat(formatDateTime(utcNow(), 'yyyyMMddHHmmss'), '_', item().name)"}, # Dynamic filename based on source filename
        format={
            "type": "DelimitedText", # Output as delimited text (e.g., CSV)
            "firstRowAsHeader": True,
            "columnDelimiter": ","
        }
    )
    adf_client.datasets.create_or_update(
        resource_group_name, data_factory_name, blob_dataset_name, blob_dataset
    )
    print(f"Created Dataset: {blob_dataset_name}")


    # 5. Create Pipeline with Copy Data Activity
    print("Creating Pipeline with Copy Data activity...")
    copy_activity = CopyActivity(
        name="CopySftpFtpToBlob",
        inputs=[DatasetReference(reference_name=sftp_ftp_dataset_name)],
        outputs=[DatasetReference(reference_name=blob_dataset_name)],
        source=FileSystemSource(), # Base source for SFTP/FTP/Blob/Local File System
        sink=BlobSink(),           # Specific sink for Blob Storage
        # Enable retry logic here!
        retry=3, # Retry 3 times
        retry_interval_in_seconds=30 # Wait 30 seconds between retries
    )
    pipeline = PipelineResource(
        activities=[copy_activity]
    )
    adf_client.pipelines.create_or_update(
        resource_group_name, data_factory_name, pipeline_name, pipeline
    )
    print(f"Created Pipeline: {pipeline_name}")

    print("\nADF resources successfully created/updated for FTP/SFTP extraction.")
    print(f"You can now go to Azure Data Factory Studio and trigger the pipeline '{pipeline_name}'.")

except Exception as e:
    print(f"An error occurred: {e}")