import os
from flask import Flask, render_template, request, redirect, url_for, abort,flash, send_from_directory, Response
from werkzeug.utils import secure_filename
from ultralytics import YOLO
import atexit
import cv2
import base64


app = Flask(__name__)
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.jpeg']
app.config['UPLOAD_PATH'] = 'static/uploads'


model = YOLO("../runs/detect/train/weights/best.pt")

# Delete uploaded files when program stops
def delete_uploaded_files():
    upload_folder = app.config['UPLOAD_PATH']
    for filename in os.listdir(upload_folder):
        file_path = os.path.join(upload_folder, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
atexit.register(delete_uploaded_files)

# Delete uploaded files with button when activated by POST request
@app.route('/delete-uploads', methods=['POST'])
def delete_uploads():
    upload_folder = app.config['UPLOAD_PATH']
    for filename in os.listdir(upload_folder):
        file_path = os.path.join(upload_folder, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
    return redirect(url_for('index'))

# HTTP GET requests and render index.html template
@app.route('/')
def index():
    upload_folder = app.config['UPLOAD_PATH']
    files = [f for f in os.listdir(upload_folder) if os.path.isfile(os.path.join(upload_folder, f))]
    return render_template('index.html', files=files)

# HTTP POST request for uploading files, stored in "static/uploads"
@app.route('/', methods=['POST'])
def upload_files():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config['UPLOAD_EXTENSIONS']:
            abort(400)
        uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
    return redirect(url_for('index'))

# display uploaded files
@app.route('/static/uploads/<filename>')
def upload(filename):
    return send_from_directory(app.config['UPLOAD_PATH'], filename)

# predict the results with YOLO model on uploaded images
@app.route('/analyze')
def analyze():
    # uploaded images in uploads folder
    uploaded_folder = app.config['UPLOAD_PATH']
    # list all uploaded files in uploads folder
    image_files = [f for f in os.listdir(uploaded_folder) if f.endswith(tuple(app.config['UPLOAD_EXTENSIONS']))]
    image_data_list = []

    # loop though images in the folder and predict
    for image_file in image_files:
        img_path = os.path.join(uploaded_folder, image_file)
        results = model.predict(img_path, save=False, stream=True)

        for r in results:
            # encode array of image to bytes
            image_bytes = cv2.imencode('.jpg', r.plot())[1].tobytes()

            # encode the imagebytes to base64-encoded string
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            # Add the base64-encoded image data to the list
            image_data_list.append(image_base64)
    return render_template('predictions.html', image_data_list=image_data_list)

if __name__ == '__main__':
    app.run(debug=True)


