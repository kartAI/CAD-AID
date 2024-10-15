from azure.ai.ml import MLClient
from azure.ai.ml.entities import Environment
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

# Create the environment using your custom Docker image from the Azure Container Registry
environment_name = "yolo-training-env"
env = Environment(
    name=environment_name,
    image="cadaidregistry.azurecr.io/yolov8-training:latest",
)

# Register the environment in the Azure ML workspace
ml_client.environments.create_or_update(env)
print(f"Environment '{environment_name}' created successfully")