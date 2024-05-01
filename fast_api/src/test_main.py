from fastapi.testclient import TestClient

from main import app
import os

client = TestClient(app)


def test_detect_objects_with_image():
    # Path to a test image file
    test_image_path = 'test_images/situasjonskart.jpg'

    if os.path.exists(test_image_path):
        print("File exists.")
    else:
        print("File does not exist.")


    files = [('uploaded_files', (os.path.basename(test_image_path), open(test_image_path, 'rb'), 'image/jpeg'))]
    response = client.post("/detect/", files=files)

    assert response.status_code == 200
    assert response.json()[0]['file_name'] == 'situasjonskart.jpg'
    assert response.json()[0]['drawing_type'] == ['situasjonskart']


def test_upload_multible_files():
    test_image_paths= ['test_images/situasjonskart.jpg', 'test_images/snitt.jpg']

    multiple_files = [('uploaded_files', (os.path.basename(test_image_paths[0]), open(test_image_paths[0], 'rb'), 'image/jpeg')),
                      ('uploaded_files', (os.path.basename(test_image_paths[1]), open(test_image_paths[0], 'rb'), 'image/jpeg'))]

    response = client.post("/detect/", files=multiple_files)

    assert response.status_code == 200


# def test_maxsize():
#     test_image_path = 'test_images/CAD-aid-DEMO.mp4' 

#     multiple_files = [('uploaded_files', (os.path.basename(test_image_path), open(test_image_path, 'rb'), 'video/mp4')),
#                       ('uploaded_files', (os.path.basename(test_image_path), open(test_image_path, 'rb'), 'video/mp4')),
#                       ('uploaded_files', (os.path.basename(test_image_path), open(test_image_path, 'rb'), 'video/mp4')),
#                       ('uploaded_files', (os.path.basename(test_image_path), open(test_image_path, 'rb'), 'video/mp4')),
#                     ]

#     response = client.post("/detect/", files=multiple_files)

#     assert response.status_code == 413

def test_not_acceptable_file_format():
    test_image_path = 'test_images/CAD-aid-DEMO.mp4' 

    multiple_files = [('uploaded_files', (os.path.basename(test_image_path), open(test_image_path, 'rb'), 'video/mp4'))]

    response = client.post("/detect/", files=multiple_files)

    assert response.json() == []

def test_detect_objects_with_pdf ():
    # Similar structure as the image test, but with a PDF file
   test_pdf_path = 'test_images/cad-aid-system-overview.pdf'

   with open(test_pdf_path, 'rb') as test_pdf:
       files = {'uploaded_files': (os.path.basename(test_pdf_path), test_pdf, 'application/pdf')}
       response = client.post("/detect/", files=files)

   assert response.status_code == 200
