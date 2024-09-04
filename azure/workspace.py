from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential, EnvironmentCredential
import os
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env.dev')
load_dotenv(env_path)

# Get environment variables
subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
resource_group = os.getenv("AZURE_RESOURCE_GROUP")
workspace_name = os.getenv("AZURE_WORKSPACE_NAME")

# Debugging: Ensure variables is not 'None'
if not subscription_id or not resource_group or not workspace_name:
    print("Please ensure that the environment variables are set.")
    print(f"Subscription ID: {subscription_id}")
    print(f"Resource Group: {resource_group}")
    print(f"Workspace Name: {workspace_name}")
    exit(1)
    
credential = EnvironmentCredential()

try:
    # Connect to Azure ML workspace
    ml_client = MLClient(
        DefaultAzureCredential(),
        subscription_id=subscription_id,
        resource_group=resource_group,
        workspace_name=workspace_name,
    )
    
    # Debugging: Print MLClient initialization details
    print(f"MLClient initialized: Subscription ID: {ml_client.subscription_id}, Resource Group: {ml_client.resource_group_name}, Workspace Name: {ml_client.workspace_name}")
    
except Exception as e:
    print(f"Failed to initialize MLClient: {e}")
    exit(1)
