import numpy as np
import os
import cv2



# split data to train folder 80%, test folder 10%, validation folder 10%
# creates train, validation and test folders
# group prefix = 3 for .jpg,.txt and .xml for the same filename
#splitfolders.ratio("images", output="data",seed=1337, ratio=(.8, .1, .1), group_prefix=None, move=False)

import os
import random
import shutil

# Define the source and destination folders
source_images_folder = "images"
source_labels_folder = "labels"
destination_folder = "data"

# Define the split ratios
train_ratio = 0.8
test_ratio = 0.1
val_ratio = 0.1

# Create destination subfolders
for folder in ["train", "test", "val"]:
    os.makedirs(os.path.join(destination_folder, folder, "images"), exist_ok=True)
    os.makedirs(os.path.join(destination_folder, folder, "labels"), exist_ok=True)

# List all image files in the source images folder
image_files = [file for file in os.listdir(source_images_folder) if file.endswith(".jpg")]

# Shuffle the image files randomly
random.shuffle(image_files)

# Calculate split indices
total_images = len(image_files)
train_split = int(train_ratio * total_images)
test_split = int(test_ratio * total_images)

# Split and move the images and labels
for i, image_file in enumerate(image_files):
    source_image_path = os.path.join(source_images_folder, image_file)
    source_label_path = os.path.join(source_labels_folder, image_file.replace(".jpg", ".txt"))

    if i < train_split:
        destination_folder_name = "train"
    elif i < train_split + test_split:
        destination_folder_name = "test"
    else:
        destination_folder_name = "val"

    destination_image_path = os.path.join(destination_folder, destination_folder_name, "images", image_file)
    destination_label_path = os.path.join(destination_folder, destination_folder_name, "labels", image_file.replace(".jpg", ".txt"))

    # Move the image and label
    shutil.copy(source_image_path, destination_image_path)
    shutil.copy(source_label_path, destination_label_path)

print("Data split and copied successfully.")