from ultralytics import YOLO
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Model, Data, JobOutput, Metric
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

# Fetch datasets from Azure Blob Storage
detection_data = ml_client.data.get(name="detection_data", version="1")
segmentation_data = ml_client.data.get(name="segmentation_data", version="1")
detection_data_path = detection_data.path
segmentation_data_path = segmentation_data.path

# Fetch registered models from Azure ML workspace
detection_model = ml_client.models.get(name="detection_model", version=3)
segmentation_model = ml_client.models.get(name="segmentation_model", version=1)
detection_model_path = detection_model.download(target_dir="models/runs/detect/nora/train6/weights", exist_ok=True)
segmentation_model_path = segmentation_model.download(target_dir="models/runs/segment/train8/weights", exist_ok=True)

# Load and train the detection model
detection_weights_path = f'{detection_model_path}/best.pt'
detection_model = YOLO(detection_weights_path)
detection_model.train(data=f'{detection_data_path}/data.yaml', epochs=50, imgsz=640, batch=16, workers=4)

# Validate the detection model
detection_metrics = detection_model.val()

# Log detection metrics
ml_client.jobs.update(
    job_name="yolo-training-job",
    outputs={"detection_metrics": Metric(name="detection_metrics", value=detection_metrics)}
)

# Save the newly trained detection weights
detection_model.export('models/runs/detect/nora/train7/weights')

# Load and train the segmentation model
segmentation_weights_path = f'{segmentation_model_path}/best.pt'
segmentation_model = YOLO(segmentation_weights_path)
segmentation_model.train(data=f'{segmentation_data_path}/data_seg.yaml', epochs=50, imgsz=640, batch=16, workers=4)

# Validate the segmentation model
segmentation_metrics = segmentation_model.val()

# Log segmentation metrics
ml_client.jobs.update(
    job_name="yolo-training-job",
    outputs={"segmentation_metrics": Metric(name="segmentation_metrics", value=segmentation_metrics)}
)

# Save the newly trained segmentation weights
segmentation_model.export('models/runs/segment/train9/weights')