from azureml.core import Workspace, Model
from azureml.core.authentication import AzureCliAuthentication
from dotenv import load_dotenv, find_dotenv
import os

# Print current working directory for debugging
print("Current working directory:", os.getcwd())

# Load environment variables
dotenv_path = find_dotenv("../.env.dev")
print("Dotenv path found:", dotenv_path)
load_dotenv(dotenv_path)

# Get workspace details
subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
resource_group = os.getenv("AZURE_RESOURCE_GROUP")
workspace_name = os.getenv("AZUREML_WORKSPACE_NAME")

# Print workspace details
print(f"Subscription ID: {subscription_id}")
print(f"Resource Group: {resource_group}")
print(f"Workspace Name: {workspace_name}")

auth = AzureCliAuthentication()

# Connect to workspace
ws = Workspace(subscription_id, resource_group, workspace_name, auth)

# Get absolute path of the model directory
model_dir = os.path.abspath("./models_to_register/detection_model/")
seg_model_dir = os.path.abspath("./models_to_register/segmentation_model/")

# Register detection model
detection_model = Model.register(
    workspace=ws,
    model_path=model_dir,
    model_name="detection_model",
    tags={'area': 'detection'},
    description="YOLO detection model"
)

print(f"Detection model registered: {detection_model.name}, version {detection_model.version}")

# Register segmentation model
segmentation_model = Model.register(
    workspace=ws,
    model_path=seg_model_dir,
    model_name="segmentation_model",
    tags={'area': 'segmentation'},
    description="YOLO segmentation model"
)

print(f"Segmentation model registered: {segmentation_model.name}, version {segmentation_model.version}")
