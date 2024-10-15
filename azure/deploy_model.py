from azure.ai.ml.entities import OnlineDeployment, ManagedOnlineEndpoint
from training.workspace import ml_client
import os

# Get environment variables
endpoint_name = os.getenv("ENDPOINT_NAME")
deployment_name = os.getenv("DEPLOYMENT_NAME")
model_name = os.getenv("MODEL_NAME")
aks_compute_name = os.getenv("AKS_COMPUTE_NAME")
prediction_image_path = os.getenv("PREDICTION_IMAGE_PATH")

# Create an endpoint for deployment
endpoint = ManagedOnlineEndpoint(
    name=endpoint_name,
    auth_mode="key"
)

# Register the endpoint
ml_client.online_endpoints.create_or_update(endpoint)

# Get the registered model ID
registered_model = ml_client.models.get(model_name)

# Define the deployment
deployment = OnlineDeployment(
    name=deployment_name,
    endpoint_name=endpoint_name,
    model=registered_model.id,
    environment_variables={
        "PREDICTION_IMAGE_PATH": prediction_image_path
    },
    compute=aks_compute_name,
    instance_type="Standard_DS3_v2",
    instance_count=1
)

# Deploy the model
ml_client.online_deployments.begin_create_or_update(deployment).result()
print(f"Model {model_name} deployed to endpoint '{endpoint_name}'.")