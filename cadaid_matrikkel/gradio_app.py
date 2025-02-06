import gradio as gr
import requests
import os

UPLOAD_DIRECTORY = "/app/upload_files"

os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


API_URL = "http://api:8000/floorplan"  # Use 'api' if that's the service name in docker-compose.yml

def save_image(image):
    file_path = os.path.join(UPLOAD_DIRECTORY, image.name)
    image.save(file_path)

def get_detections(image):
    #files = [("uploaded_files", (file.name, file)) for file in uploaded_files]
    file_path = os.path.join(UPLOAD_DIRECTORY, image.name)
    image.save(file_path)
    
    with open(file_path, "rb") as img_file:
        response = requests.post(API_URL, files={"file": img_file})
    
    return response.json()
    """files = [("uploaded_files", (file.name, file)) for file in uploaded_files]
   
    print("files gradio", files)
    
    # Send the POST request to the FastAPI endpoint
    response = requests.post(API_URL, files=files)
    
    # Check if the request was successful
    if response.status_code == 200:
        return response.json()  # Return the JSON response
    else:
        return f"Error: {response.text}"""

# Create the Gradio interface
with gr.Blocks() as app:
    gr.Markdown("## Floorplan Detection App")

    with gr.Row():
        #image_input = gr.File(label="Upload Floorplan Images", file_count="multiple")
        image_input = gr.Image(type="pil")
        submit_button = gr.Button("Submit")
        output = gr.Textbox()
    
    #output = gr.JSON(label="Detection Results")
    
    # Set the button click event
    submit_button.click(get_detections, inputs=image_input, outputs=output)

# Launch the Gradio app
app.launch()

"""def upload_file(files):
    file_paths = [file.name for file in files]
    return file_paths

with gr.Blocks() as demo:
    file_output = gr.File()
    upload_button = gr.UploadButton("Click to Upload a File", file_types=["image", "video"], file_count="multiple")
    upload_button.upload(upload_file, upload_button, file_output)

demo.launch()"""