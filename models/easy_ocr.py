
from PIL import Image, ImageDraw

import easyocr
import cv2
import argparse
import sys

from Levenshtein import distance as levenshtein_distance


# Get detected bbox and text from image
def easy_ocr_detection(image):
	reader = easyocr.Reader(['no'])
	results = reader.readtext(image)

	detected_text = []

	for result in results:
		bbox,text,prob = result
		text_info = {
			"text": text,
			"bbox": bbox,
			"probability": prob
		}
		detected_text.append(text_info)
	return detected_text

# Plot the detected bboxes for text in image
def plot_text_bboxes(detected_text_list, image):
	for text_info in detected_text_list:
		# bbox: [[x1,y1],[x2,y2], [x3,y3], [x4,y4]]
		bbox = text_info["bbox"]
		# get top left [x1,y1]
		top_left = tuple(bbox[0])
		# bottom right [x3,y3]
		bottom_right = tuple(bbox[2])

		# draw green rectangle (0,255,0) and thickness 2
		cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)

	# Display the image with bounding boxes
	cv2.imshow('Detected Text', image)
	cv2.waitKey(0)
	cv2.destroyAllWindows()


# Read the hard coded text we want to compare
def read_text_files(file_path):
	text_from_files = []
	with open(file_path, "r") as file:
		for line in file:
			string = line.strip()
			text_from_files.append(string)
	return text_from_files

# General similarity check for detected words and target words
def search_word(text_info_list, target_words):

	similarity_threshold = 2  # Define how similar a word must be (lower means more similar)

	similar_words_info = []

	for text_info in text_info_list:
		text = text_info["text"]  # Extract the text from the dictionary
		for target in target_words:
			if levenshtein_distance(text.lower(), target.lower()) <= similarity_threshold:
				# Store the whole dictionary if similar, which includes text, bbox, and probability
				similar_words_info.append(text_info)
				break  # Break to avoid adding the same text multiple times if it matches multiple targets


	return similar_words_info

# Similarity check specifically for scales
def check_scales(decoded_text, target_words):
	similar_words = []

	for word in decoded_text:
		text = word["text"].lower()

		for target in target_words:

			if text == target.lower() and text not in similar_words:
				similar_words.append(text)
				break


	return similar_words

if __name__ == "__main__":
	image_path = '../data/train/images/fasade32.jpg'
	image = cv2.imread(image_path)

	# list of dictionaries containing text,bbox and prob
	detected_text = easy_ocr_detection(image)
	plot_text_bboxes(detected_text,image)

	orientations = read_text_files("../text_in_drawings_dictionary/himmelretninger.txt")
	scales = read_text_files("../text_in_drawings_dictionary/scale.txt")
	room_names = read_text_files("../text_in_drawings_dictionary/plantegninger.txt")

	detected_orientations = search_word(detected_text, orientations)
	detected_scales = check_scales(detected_text,scales)
	detected_rooms = search_word(detected_text,room_names)
	print(detected_rooms)

	plot_text_bboxes(detected_rooms,image)





