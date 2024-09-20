import requests
import os
from dotenv import load_dotenv

# This script tests the Azure endpoint for the CAD-AID project

# Load environment variables from .env.dev file
load_dotenv(".env.dev")

# Get Azure-specific environment variables
endpoint_name = os.getenv("ENDPOINT_NAME")
api_key = os.getenv("API_KEY")
location = os.getenv("AZURE_LOCATION")

# Construct the scoring URI for the Azure endpoint
scoring_uri = f"https://{endpoint_name}.{location}.inference.ml.azure.com/analyze"

# Set up headers with the API key for authentication
headers = {"Authorization": f"Bearer {api_key}"}

# Prepare the test image file
file_path = "../data/test/images/Galtavikveien13_plan3_page_1.jpg"
files = {"file": open(file_path, "rb")}

# Send a POST request to the Azure endpoint and print the response
response = requests.post(scoring_uri, headers=headers, files=files)
print(response.json())

