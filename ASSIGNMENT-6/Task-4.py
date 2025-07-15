import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import (
    TriggerResource,
    ScheduleTrigger,
    PipelineReference,
    ScheduleTriggerRecurrence,
    DayOfWeek,
    ScheduleDay
)

# --- Configuration ---
# Replace with your actual values
subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID", "YOUR_SUBSCRIPTION_ID")
resource_group_name = "your-adf-resource-group"  # The resource group where your ADF is
data_factory_name = "your-adf-name"              # Your Azure Data Factory name
pipeline_name_to_trigger = "Pipeline_OnPremToAzureSql" # The name of the pipeline you want to trigger
trigger_name = "Trigger_LastSaturdayOfMonth"
location = "East US" # Or your ADF region

# --- Azure Authentication ---
credential = DefaultAzureCredential()

# --- Data Factory Management Client ---
adf_client = DataFactoryManagementClient(credential, subscription_id)

print(f"Connecting to Azure Data Factory: {data_factory_name} in {resource_group_name}")

try:
    # Define the recurrence for the last Saturday of the month
    # This sets the trigger to fire monthly, specifically on Saturday,
    # and only for the 'Last' occurrence of Saturday within that month.
    schedule_recurrence = ScheduleTriggerRecurrence(
        frequency="Month",  # Recur monthly
        interval=1,         # Every 1 month
        week_days=[DayOfWeek.SATURDAY], # On Saturdays
        # The 'monthly_occurrences' list is key for "last Saturday"
        # It specifies that we want the 'Last' occurrence of 'Saturday'
        monthly_occurrences=[
            ScheduleDay(
                day_of_week=DayOfWeek.SATURDAY,
                occurrence="Last"
            )
        ],
        start_time="2024-01-01T00:00:00Z",  # Start time in UTC. Adjust as needed.
        # You can also add end_time if needed: end_time="2025-12-31T23:59:59Z"
    )

    # Create the Schedule Trigger resource
    trigger = TriggerResource(
        properties=ScheduleTrigger(
            pipeline=PipelineReference(
                reference_name=pipeline_name_to_trigger,
                type="PipelineReference"
            ),
            recurrence=schedule_recurrence,
            # Add a description for clarity
            description="Triggers the pipeline on the last Saturday of every month."
        )
    )

    # Create or update the trigger in Azure Data Factory
    print(f"Creating/Updating Trigger: {trigger_name} for Pipeline: {pipeline_name_to_trigger}...")
    adf_client.triggers.create_or_update(
        resource_group_name,
        data_factory_name,
        trigger_name,
        trigger
    )
    print(f"Trigger '{trigger_name}' created/updated successfully.")

    # To start the trigger, you need to set its state to 'Started'
    # By default, when created, it might be in 'Stopped' state.
    print(f"Starting Trigger: {trigger_name}...")
    adf_client.triggers.start(resource_group_name, data_factory_name, trigger_name)
    print(f"Trigger '{trigger_name}' started.")

    print("\nAutomation complete. The pipeline will now trigger every last Saturday of the month.")

except Exception as e:
    print(f"An error occurred: {e}")