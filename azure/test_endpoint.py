import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.dev")

# Get environment variables
endpoint_name = os.getenv("ENDPOINT_NAME")
api_key = os.getenv("API_KEY")
location = os.getenv("AZURE_LOCATION")

scoring_uri = f"https://{endpoint_name}.{location}.inference.ml.azure.com/analyze"
headers = {"Authorization": f"Bearer {api_key}"}

# Prepare the data
file_path = "../data/test/images/Galtavikveien13_plan3_page_1.jpg"
files = {"file": open(file_path, "rb")}

response = requests.post(scoring_uri, headers=headers, files=files)
print(response.json())

