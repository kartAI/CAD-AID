import cv2
from ultralytics import YOLO
from models.nora import prediction_nora
from models.easy_ocr import easy_ocr_detection, search_word,read_text_files, check_scales
from models.eva import predict_seg

# Sjekk type tegning fra nora modellen
def check_drawings(results, decoded_text):

    for r in results:

        r_array = r.numpy()
        boxes = r_array.boxes.xyxy
        labels = r_array.boxes.cls

        fasade_scale = []
        fasade_himmelretninger = []

        for box, label in zip(boxes, labels):

            if int(label) == 0:  # Check if the label is 0 - fasade
                detected_scales, detected_orientation = check_elevation_requirements(decoded_text)
                if detected_scales not in fasade_scale:
                    fasade_scale.append(detected_scales)
                if detected_orientation not in fasade_himmelretninger:
                    fasade_himmelretninger.append(detected_orientation)





        print("Himmelretninger:", fasade_himmelretninger)
        print("Målestokk: ", fasade_scale)


# Krav til fasade
def check_elevation_requirements(decoded_text):

    # read scales from text file (temporary solution)
    read_scales = read_text_files("text_in_drawings_dictionary/scale.txt")

    # Check if scale is in the image
    detected_scales = check_scales(decoded_text, read_scales)

    # read orientation from text file (temporary solution)
    read_orientations = read_text_files("text_in_drawings_dictionary/himmelretninger.txt")

    # Check if orientations in drawing:
    detected_orientations = search_word(decoded_text,read_orientations)

    return detected_scales, detected_orientations


if __name__ == "__main__":
    img_path= "data/test/images/Draugveien 173B_snitt_page_7.jpg"

    model = YOLO("runs/detect/nora/train2/weights/best.pt")
    # Get the predicted drawing types
    predicted_drawings = prediction_nora(img_path,model)

    # Read text in image and check if meets requirements
    image = cv2.imread(img_path)
    bounding_boxes, decoded_text = easy_ocr_detection(image)
    check_drawings(predicted_drawings, decoded_text)



