from azureml.core import Workspace
from azureml.core.compute import AksCompute, ComputeTarget
from azureml.core.compute_target import ComputeTargetException
import os
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env.dev')
load_dotenv(env_path)  # Ensure you are loading the file from the correct path

# Get environment variables
subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
resource_group = os.getenv("AZURE_RESOURCE_GROUP")
workspace_name = os.getenv("AZURE_WORKSPACE_NAME")
aks_compute_name = os.getenv("AKS_COMPUTE_NAME")
aks_cluster_name = os.getenv("AKS_CLUSTER_NAME")
aks_location = os.getenv("AKS_LOCATION")

# Debugging: Print environment variables
print(f"Subscription ID: {subscription_id}")
print(f"Resource Group: {resource_group}")
print(f"Workspace Name: {workspace_name}")
print(f"AKS Compute Name: {aks_compute_name}")
print(f"AKS Cluster Name: {aks_cluster_name}")
print(f"AKS Location: {aks_location}")

# Connect to Azure ML workspace
ws = Workspace.get(
    name=workspace_name,
    subscription_id=subscription_id,
    resource_group=resource_group
)

# Check if the AKS compute target already exists
try:
    aks_target = AksCompute(ws, aks_compute_name)
    print(f"Found existing AKS compute target: {aks_compute_name}")
except ComputeTargetException:
    print(f"AKS compute target {aks_compute_name} not found. Attaching to existing AKS cluster...")
    
    # Specify the resource ID of the existing AKS cluster
    cluster_resource_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.ContainerService/managedClusters/{aks_cluster_name}"
    
    # Debugging: Print cluster resource ID
    print(f"Cluster Resource ID: {cluster_resource_id}")

    # Attach existing AKS cluster
    prov_config = AksCompute.attach_configuration(
        resource_id=cluster_resource_id
    )
    
    # Attach AKS cluster to Azure ML workspace
    aks_target = ComputeTarget.attach(ws, aks_compute_name, prov_config)
    aks_target.wait_for_completion(show_output=True)
    print(f"Attached AKS compute target: {aks_compute_name}")
