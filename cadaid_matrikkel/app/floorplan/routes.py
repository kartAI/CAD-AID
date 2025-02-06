
from fastapi import FastAPI, APIRouter, UploadFile, File
from  fastapi.responses import JSONResponse
import os
import shutil
from typing import List
from pdf2image import convert_from_path
import cv2
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image
from app.floorplan.model import Segmentation, OCRModel
from app.floorplan.utils import Floorplan, crop_image, filter_text_within_object, preprocess_image
from app.floorplan.data_structures import FloorplanDetection, FileDetections, ObjectDetectionResults, OCRDetections, SegmentationResults
from app.classification.model import ObjectDetection



UPLOAD_DIRECTORY = "/app/upload_files"
OUTPUT_DIR = "/app/upload_files"

os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


router = APIRouter()

app = FastAPI()

segmentation = Segmentation()
objdet_model = ObjectDetection()
floorplan = Floorplan()
ocr = OCRModel()

@router.post("/")
async def process_floorplan(uploaded_files: List[UploadFile]):
    all_detections = []
    for uploaded_file in uploaded_files:
      
        #file_path = f"/app/upload_files/{uploaded_file.filename}"
      
        #file_path = f"{UPLOAD_DIRECTORY}/{uploaded_file.filename}"
        file_path = os.path.join(UPLOAD_DIRECTORY, uploaded_file.filename)
        print(f"File path: {file_path}")
        with open(file_path, "wb") as file_object:
            #file_object.write(uploaded_file.file.read())
            file_object.write(await uploaded_file.read())  # Use await for async read

    
        if uploaded_file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            image = cv2.imread(file_path)
            results = segmentation.process_results(image)
            drawing_types, bboxes, confidences = objdet_model.process_results(image)
            
            for drawing_type, bbox, confidence in zip(drawing_types,bboxes,confidences):
                if drawing_type == "plantegning":
                    
                    object_detections = ObjectDetectionResults(drawing_type=drawing_type, bbox=bbox, probability=confidence)
                    
                    
                    segmentation_results = segmentation.process_results(image)
                    seg_detections = SegmentationResults()
                    seg_detections.count_rooms(segmentation_results, bbox)

                    seg_masks = seg_detections.masks

                   
                    extracted_text = ocr.perform_ocr(image, language='nor')

                    for text in extracted_text:
                        print(text.text)

                    # extract text only within plantegning bbox
                    text_within_object = filter_text_within_object(extracted_text, bbox)


                    # Kun OCR
                    oppholdsrom = floorplan.get_rooms_text(text_within_object, file_path="vocabulary/oppholdsrom.txt")
                    bad = floorplan.get_rooms_text(text_within_object, file_path = "vocabulary/baderom.txt")
                    kjokken = floorplan.get_rooms_text(text_within_object, file_path = "vocabulary/kjokken.txt" )
                   

                    extracted_int_text = ocr.perform_ocr(image, language='eng')
                    alle_rom = floorplan.get_rooms_text(text_within_object, file_path="vocabulary/alle_rom.txt")
                    
                    
                    text_int_in_bbox = filter_text_within_object(extracted_int_text, bbox)
                    arealer = floorplan.get_area_info(text_within_object, alle_rom, seg_masks)
                   
                    bra = floorplan.get_BRA_info(extracted_text)
                    bya = floorplan.get_BYA_info(extracted_text)
                    
                
                    ocr_detections = OCRDetections(rooms=oppholdsrom,all_rooms=alle_rom, bathrooms=bad, kitchens=kjokken, arealer=arealer)
                    ocr_detections.update_total_rooms()
                    ocr_detections.update_bathroom_count()

                    if bra:
                        ocr_detections.BRA = bra
                    else:
                        ocr_detections.update_BRA()
                    
                    if bya:
                        ocr_detections.BYA = bya
                    else:
                        ocr_detections.BYA = None


                    
            
                    all_detections.append(FileDetections(filename=uploaded_file.filename, 
                                                 objdet=object_detections,
                                                 ocr=ocr_detections,
                                                 segmentation = seg_detections
                                                 ))
    return all_detections
    





