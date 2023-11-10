import cv2
import pytesseract
import re
from pytesseract import Output
def check_directional_words(text):
    himmelretning = ["nord", "vest", "øst", "sør"]
    detektert_himmeretning = []
    for word in himmelretning:
        if word in text.lower():
            detektert_himmeretning.append(word)
    if not detektert_himmeretning:
        print("Tegningen mangler himmelretning")
    else:
        print("Himmelretninger",detektert_himmeretning)
def detect_scale(text):

    # Define regular expressions to match the scales
    scale_patterns = [r'\s*:\s*100', r'\s*:\s*50', r'\s*:\s*200', r'\s*:\s*500']
    text = text.replace('\n', ' ').strip()

    # Check if any of the patterns match the extracted text
    for pattern in scale_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            detected_scale = re.findall(pattern, text, re.IGNORECASE)[0]
            # Add "1:" in front of the detected scale
            detected_scale_with_prefix = f"1{detected_scale}"
            return True, detected_scale_with_prefix

    return False, None
def detect_drawing_type(text):
    tegning_tittel = ["fasade","etasje", "etg","plan","snitt","situasjonsplan","situasjonskart"]
    detetektert_tittel=[]

    for tittel in tegning_tittel:
        if tittel in text.lower():
            detetektert_tittel.append(tittel)
    if not detetektert_tittel:
        print("Type tegning ikke funnet")
    else:
        print("Type tegning:",detetektert_tittel)


def check_orientation(image):
    output = pytesseract.image_to_osd(image)

    angle_match = re.search(r'Orientation in degrees: (\d+)', output)
    confidence_match = re.search(r'Orientation confidence: (\d+\.\d+)', output)

    if angle_match and confidence_match:
        angle = angle_match.group(1)
        confidence = float(confidence_match.group(1))

        if confidence > 2.0:
            if angle == '90':
                rotated_image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            elif angle == '180':
                rotated_image = cv2.rotate(image, cv2.ROTATE_180)
            elif angle == '270':
                rotated_image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
            else:
                rotated_image = image  # No need to rotate

            return rotated_image  # Return the rotated image

            # Now 'rotated_image' contains the corrected image
        else:
            print('Low confidence in rotation angle prediction')
    else:
        print('Rotation angle not found in Tesseract train_test_val')
    return None # when conf low or angle not found


# Load the image
image = cv2.imread('../images/plantegning/plantegning5_page_1.jpg')


#check angle
image=check_orientation(image)


# Convert the image to grayscale
gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


# Use Tesseract to extract text from the image
text = pytesseract.image_to_string(gray_image, lang='nor', config='--psm 6')


# Check if the image contains himmeretning
check_directional_words(text)

detect_drawing_type(text)
# check if image has scale (mål)
has_scale, detected_scale = detect_scale(text)

if has_scale:
    print(f"The image contains the scale: {detected_scale}")
else:
    print("No scale detected in the image.")