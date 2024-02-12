from fastapi.testclient import TestClient

from main import app
import os

client = TestClient(app)


def test_detect_objects_with_image():
    # Path to a test image file
    test_image_path = 'static/uploads/2Enebolig_page_1.jpg'

    if os.path.exists(test_image_path):
        print("File exists.")
    else:
        print("File does not exist.")

    # Open the test image file in binary mode
    with open(test_image_path, 'rb') as test_image:
        # Create a dict to simulate form data_old with a file upload
        files = {'uploaded_file': (os.path.basename(test_image_path), test_image, 'image/jpeg')}

        # Send a POST request to the endpoint with the test image
        response = client.post("/detect/", files=files)

    # Verify the status code of the response
    assert response.status_code == 200

    # Parse the response JSON and perform further checks as needed
    detections = response.json()['detections']
    assert len(detections) > 0  # Example check: ensure at least one detection was made


#def test_detect_objects_with_pdf ():
    # Similar structure as the image test, but with a PDF file
#    test_pdf_path = 'static/uploads/Tegning20ny20fasade.PDF'

#    with open(test_pdf_path, 'rb') as test_pdf:
#        files = {'uploaded_file': (os.path.basename(test_pdf_path), test_pdf, 'application/pdf')}
#        response = client.post("/detect/", files=files)

#    assert response.status_code == 200
#    # Add assertions to verify PDF handling
