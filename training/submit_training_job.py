from azure.ai.ml import MLClient
from azure.ai.ml.entities import AmlCompute, Environment, Job, Command
from azure.identity import DefaultAzureCredential
import os
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env.dev')
load_dotenv(env_path)

# Get environment variables
subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
resource_group = os.getenv("AZURE_RESOURCE_GROUP")
workspace_name = os.getenv("AZUREML_WORKSPACE_NAME")

# Initialize MLClient
ml_client = MLClient(
    DefaultAzureCredential(),
    subscription_id=subscription_id,
    resource_group_name=resource_group,
    workspace_name=workspace_name,
)

# Submit the job using the YAML configuration file