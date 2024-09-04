from azure.identity import DefaultAzureCredential
from azure.ai.ml.entities import Model
import os
from dotenv import load_dotenv
from workspace import ml_client


# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env.dev')
print(f"Loading environment from: {env_path}")  # Debugging line
load_dotenv(env_path)

# Reuse ml_client directly
try:
    print(f"MLClient details: Subscription ID: {ml_client.subscription_id}, Resource Group: {ml_client.resource_group_name}, Workspace Name: {ml_client.workspace_name}")
    print("Successfully reused MLClient.")
except Exception as e:
    print(f"Failed to reuse MLClient: {e}")
    exit(1)

# Register Docker image as a model
try:
    model = Model(
        name=os.getenv("MODEL_NAME"),
        version=os.getenv("MODEL_VERSION"),
        type="custom_model",
        path=f"azureml://registries/{os.getenv('ACR_NAME')}/repositories/cadaidbackend/latest"
    )

    # Register model in Azure ML
    registered_model = ml_client.models.create_or_update(model)
    print(f"Model {model.name} registered with version {model.version}.")
except Exception as e:
    print(f"An error occurred while registering the model: {e}")
