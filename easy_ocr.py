
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

	bounding_boxes = []
	decoded_labels = []

	for result in results:
		bounding_boxes.append(result[0])
		decoded_labels.append(result[1])

	print(decoded_labels)
	print(bounding_boxes)
	return decoded_labels

# Plot the detected bboxes for text in image
def plot_text_bboxes(bounding_boxes, image):
	for bbox in bounding_boxes:
		top_left = tuple(map(int, bbox[0]))
		bottom_right = tuple(map(int, bbox[2]))
		cropped_image = image[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
		cropped_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)

		# Convert to PIL Image
		cropped_image_pil = Image.fromarray(cropped_image)

		image = cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)

	# Display the image with bounding boxes
	cv2.imshow('Detected Text', image)
	cv2.waitKey(0)
	cv2.destroyAllWindows()


# Read the hard coded text we want to compare for scales
def read_scale_from_file(file_path):
	scales = []

	with open(file_path, "r") as file:
		for line in file:
			scale = line.strip()
			scales.append(scale)

	return scales


# Les inn himmelretninger fra tekst fil
def read_orientations_from_file(file_path):
	orientations = []
	with open(file_path, "r") as file:
		for line in file:
			orientation = line.strip()
			orientations.append(orientation)

	return orientations

# General similarity check for detected words and target words
def search_word(decoded_text, target_words):

	similarity_threshold = 1.5  # Define how similar a word must be (lower means more similar)

	similar_words = []

	for word in decoded_text:
		for target in target_words:
			if levenshtein_distance(word.lower(), target.lower()) <= similarity_threshold:
				if word in similar_words:
					break
				else:
					similar_words.append(word)
				break  # Break to avoid adding the same word multiple times if it matches multiple targets

	return similar_words

# Similarity check specifically for scales
def check_scales(decoded_text, target_words):
	similar_words = []

	for word in decoded_text:
		detected_word = word.replace(" ", "").lower()

		for target in target_words:
			target_word = target.replace(" ", "").lower()

			if detected_word == target_word and detected_word not in similar_words:
				similar_words.append(detected_word)
				break


	return similar_words


if __name__ == "__main__":
	image_path = 'data/test/images/fasade37.jpg'
	image = cv2.imread(image_path)
	bounding_boxes,decoded_text= easy_ocr_detection(image)



