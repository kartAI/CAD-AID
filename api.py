from fastapi import FastAPI, File, UploadFile, HTTPException
from utils.detection_handler import DetectionHandler
from utils.detection_handler import SegmentationHandler
from dotenv import load_dotenv
import os
import shutil
import uuid
import logging
from azureml.core import Workspace, Model
from azureml.core.authentication import AzureCliAuthentication, MsiAuthentication
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename='/app/logs/app.log', filemode='a',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
logger.info("Loading environment variables from .env.dev")
load_dotenv(".env.dev")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the detection handler
logger.info("Initializing detection handler")
detection_handler = DetectionHandler()

# Azure ML workspace details
subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
resource_group = os.getenv("AZURE_RESOURCE_GROUP")
workspace_name = os.getenv("AZUREML_WORKSPACE_NAME")

logger.debug(f"Subscription ID: {subscription_id}")
logger.debug(f"Resource Group: {resource_group}")
logger.debug(f"Workspace Name: {workspace_name}")

# Detection Model parameters
detection_model_name = os.getenv("OBJECT_DETECTION_MODEL_NAME")
detection_model_version = os.getenv("OBJECT_DETECTION_MODEL_VERSION")

# Segmentation Model parameters
segmentation_model_name = os.getenv("SEGMENTATION_MODEL_NAME")
segmentation_model_version = os.getenv("SEGMENTATION_MODEL_VERSION")

def download_models():
    try:
        # Authenticate using Managed Identity
        logger.info("Authenticating using Managed Identity")
        msi_auth = MsiAuthentication()
        ws = Workspace(subscription_id=subscription_id,
                       resource_group=resource_group,
                       workspace_name=workspace_name,
                       auth=msi_auth)
        
        # Download detection model
        logger.info(f"Downloading detection model {detection_model_name} version {detection_model_version}")
        detection_model = Model(ws, name=detection_model_name, version=detection_model_version)
        detection_model_path = f"models/{detection_model_name}"
        detection_model.download(target_dir=detection_model_path, exist_ok=True)
        print(f"Downloaded model {detection_model_name} to {detection_model_path}")
        logger.info(f"Downloaded model {detection_model_name} to {detection_model_path}")

        # Download segmentation model
        logger.info(f"Downloading segmentation model {segmentation_model_name} version {segmentation_model_version}")
        segmentation_model = Model(ws, name=segmentation_model_name, version=segmentation_model_version)
        segmentation_model_path = f"models/{segmentation_model_name}"
        segmentation_model.download(target_dir=segmentation_model_path, exist_ok=True)
        print(f"Downloaded model {segmentation_model_name} to {segmentation_model_path}")
        logger.info(f"Downloaded model {segmentation_model_name} to {segmentation_model_path}")

        return detection_model_path, segmentation_model_path
    
    except Exception as e:
        logger.error(f"Error downloading models: {str(e)}")
        raise

@app.on_event("startup")
def startup_event():
    try:
        # Download both models at startup
        logger.info("Downloading models at startup")
        detection_model_path, segmentation_model_path = download_models()

        # Initialize the detection handler
        global detection_handler
        logger.info("Initializing detection handler")
        detection_handler = DetectionHandler(
            model_path=os.path.join(detection_model_path, 'best.pt'),
            config_path=os.path.join(detection_model_path, 'data.yaml')
        )

        # Initialize the segmentation handler
        global segmentation_handler
        logger.info("Initializing segmentation handler")
        segmentation_handler = SegmentationHandler(
            model_path=os.path.join(segmentation_model_path, 'best.pt'),
            config_path=os.path.join(segmentation_model_path, 'data.yaml')
        )
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.post("/detect/")
async def detect(file: UploadFile = File(...)):
    try:
        # Save uploaded file to disk
        file_location = f"temp_files/{file.filename}"
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Uploaded file saved to {file_location}")
            
        # Update the prediction image path in the environment variable
        os.environ["PREDICTION_IMAGE_PATH"] = file_location
        
        # Run detection
        logger.info("Running detection")
        detection_handler.check_and_execute()
        
        # Return results
        return {"filename": file.filename, "detection": "Detection completed successfully."}
    except Exception as e:
        logger.error(f"Error during detection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/segment/")
async def segment(file: UploadFile = File(...)):
    try:
        # Save uploaded file to disk
        file_location = f"temp_files/{file.filename}"
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Uploaded file saved to {file_location}")
            
        # Update the prediction image path in the environment variable
        os.environ["PREDICTION_IMAGE_PATH"] = file_location
        
        # Initialize the segmentation handler
        logger.info("Initializing segmentation handler")
        segmentation_handler = detection_handler.segmentation_handler
        
        room_text_infos = segmentation_handler.find_text_segments([])
        true_count, false_count = segmentation_handler.count_rooms()
        
        # Return segmentation results
        return {"filename": file.filename, "segmentation": "Segmentation completed successfully.", "rooms_with_labels": true_count, "rooms_without_labels": false_count}
    
    except Exception as e:
        logger.error(f"Error during segmentation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        