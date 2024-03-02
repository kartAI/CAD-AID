from models.eva import predict_seg, combine_img_masks, mask_contours, plot_contoured_masks, resize_mask
from ultralytics import YOLO
import cv2
from models.easy_ocr import easy_ocr_detection, plot_text_bboxes,read_text_files, search_word
import numpy as np
from PIL import Image


# Check if detected room text is inside bounding box for each room
def check_text_inside_room(detected_text_list,results):
    for r in results:
        room_bboxes = r.boxes.xyxy.numpy()
        # Loop through each bounding box from segmentation model
        for room_bbox in room_bboxes:
            room_name_found = False

            # Loop through list of dictionaries from Easy OCR
            for text_info in detected_text_list:
                # Get the text bboxes
                text_bbox = text_info["bbox"]
                text_x_min, text_y_min = text_bbox[0]  # Top-left corner
                text_x_max, text_y_max = text_bbox[2]  # Bottom-right corner

                # If top-left corner of text box below room bbox top left corner, and bottom right corner
                if (text_x_min >= room_bbox[0] and text_x_max <= room_bbox[2] and
                        text_y_min >= room_bbox[1] and text_y_max <= room_bbox[3]):
                    print("Rombenevnelse eksisterer")
                    room_name_found = True
                    break  # Exit loop and continue to next room
            if not room_name_found:
                print("Fant ikke rombenevnelse")


if __name__ == "__main__":
    model_segment = YOLO("runs/segment/train14/weights/best.pt")

    img_path = "data_seg/test/images/svart-hvit-2d-plantegning-med-mal.jpg"
    img = cv2.imread(img_path)

    # get text and bboxes
    detected_text= easy_ocr_detection(img)

    # get masks resized to original image
    segmentation_results = predict_seg(img,model_segment)

    # Get a list of all detected room names and coordinates
    room_names_path = "text_in_drawings_dictionary/plantegninger.txt"
    room_names = read_text_files(room_names_path)

    detected_rooms = search_word(detected_text, room_names)
    check_text_inside_room(detected_rooms,segmentation_results)




