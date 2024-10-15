from azureml.core import Datastore, Dataset, Workspace

# Load your Azure ML workspace
ws = Workspace.from_config()

# Get the default datastore in the workspace
datastore = ws.get_default_datastore()

# Upload training and validation data to the datastore for detection model
datastore.upload(src_dir='data', target_path='data', overwrite=True)

# Upload training and validation data to the datastore for segmentation model
datastore.upload(src_dir='data_seg', target_path='data_seg', overwrite=True)

print("Data uploaded to datastore")

