from models.eva import predict_seg, combine_img_masks, plot_contoured_masks, resize_mask
from ultralytics import YOLO
import cv2
from models.easy_ocr import easy_ocr_detection, plot_text_bboxes,read_text_files, search_word
import numpy as np
from PIL import Image


# Check if detected room text is inside bounding box for each room
def check_text_inside_room(detected_text_list,yolo_results):
    rooms_found = []
    for r in yolo_results:
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

                    room_name_found = True
                    break  # Exit loop and continue to next room

            rooms_found.append(room_name_found)

    for room, found in enumerate(rooms_found):
        print(f"Room {room + 1}: {'True' if found else 'False'}")

    return rooms_found

# Plot bboxes for rooms where room name is missing
def plot_bboxes_roomname_missing(detected_text_list, yolo_results, image):
    for r in yolo_results:
        yolo_bboxes = r.boxes.xyxy.numpy()  # Convert to NumPy array for easier handling

        for yolo_bbox in yolo_bboxes:
            found_text_in_room = False

            for text_info in detected_text_list:
                text_bbox_points = text_info["bbox"]
                text_x_min, text_y_min = text_bbox_points[0]  # Top-left corner
                text_x_max, text_y_max = text_bbox_points[2]  # Bottom-right corner

                # Check if the text bounding box is inside the YOLO bounding box
                if (text_x_min >= yolo_bbox[0] and text_x_max <= yolo_bbox[2] and
                    text_y_min >= yolo_bbox[1] and text_y_max <= yolo_bbox[3]):
                    found_text_in_room = True
                    break  # Found a text box inside the room, no need to check further

            if not found_text_in_room:
                # Convert YOLO bbox coordinates to integer for drawing
                yolo_bbox = yolo_bbox.astype(int)
                # Draw the YOLO bounding box on the image
                cv2.rectangle(image, (yolo_bbox[0], yolo_bbox[1]), (yolo_bbox[2], yolo_bbox[3]), (0, 255, 0), 2)
                text_x = yolo_bbox[0]
                text_y = yolo_bbox[1] - 10  # Position the text above the top-left corner of the bounding box

                # Add "Missing room label" text
                cv2.putText(image, "Mangler rombenevnelse", (text_x, max(text_y, 0)), cv2.FONT_HERSHEY_COMPLEX,
                            0.5, (0, 0, 255), 1)

    # Display the image with bounding boxes where no text is found
    cv2.imshow('Bounding Boxes Without Text', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    model_segment = YOLO("runs/segment/train14/weights/best.pt")

    img_path = "data_seg/test/images/svart-hvit-2d-plantegning-med-mal.jpg"
    img_path_no_roomlabels = "data_seg/test/images/hus-plantegning-svart-hvit.jpg"
    img_path_missing_room = "data_seg/test/images/svart-hvit-plantegning_mangler_rom.jpg"

    img = cv2.imread(img_path_missing_room)

    # get text and bboxes
    detected_text= easy_ocr_detection(img)
    # Get a list of all detected room names and coordinates
    room_names_path = "text_in_drawings_dictionary/plantegninger.txt"
    room_names = read_text_files(room_names_path)

    detected_rooms = search_word(detected_text, room_names)

    # predict segmentations and bboxes
    segmentation_results = predict_seg(img, model_segment)

    # Check if bbox for text is inside room bboxes
    check_text_inside_room(detected_rooms, segmentation_results)

    # Plot detected text
    #plot_text_bboxes(detected_rooms, img)

    # Plot rectangle for rooms with missing room name
    img_copy = img.copy()
    #plot_bboxes_roomname_missing(detected_rooms,segmentation_results,img_copy)








