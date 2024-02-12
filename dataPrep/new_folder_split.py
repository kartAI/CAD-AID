import os
import shutil
import random


# Base directory (parent of the 'data_prep' directory)
base_dir = os.path.dirname(os.path.dirname(__file__))

# Training data directories
train_images_dir = os.path.join(base_dir, "data", "train", "images")
train_labels_dir = os.path.join(base_dir, "data", "train", "labels")

# Testing data directories
test_images_dir = os.path.join(base_dir, "data", "test", "images")
test_labels_dir = os.path.join(base_dir, "data", "test", "labels")

# Validation data directories
val_images_dir = os.path.join(base_dir, "data", "val", "images")
val_labels_dir = os.path.join(base_dir, "data", "val", "labels")

# New data directories
new_images_dir = os.path.join(base_dir, "images")
new_labels_dir = os.path.join(base_dir, "labels")

def split_and_add_new_data(new_images_dir, new_labels_dir, train_ratio=0.8, test_ratio=0.1):

    # List all new image files
    valid_ext = [".jpg",".jpeg", ".png", ".JPG", ".PNG", ".JPEG"]
    new_image_files = [f for f in os.listdir(new_images_dir) if (f.endswith(ext) for ext in valid_ext)]
    random.shuffle(new_image_files)

    # Calculate split indices
    total_new_images = len(new_image_files)
    train_split_idx = int(total_new_images * train_ratio)
    test_split_idx = train_split_idx + int(total_new_images * test_ratio)


    def move_files(files, src_img_dir, src_lbl_dir, dest_img_dir, dest_lbl_dir):
        for f in files:
            shutil.move(os.path.join(src_img_dir, f), os.path.join(dest_img_dir, f))
            file_ext = os.path.splitext(f)[1]
            label_file = f.replace(file_ext, ".txt")
            shutil.move(os.path.join(src_lbl_dir, label_file), os.path.join(dest_lbl_dir, label_file))

    # Split and move new images and labels
    move_files(new_image_files[:train_split_idx], new_images_dir, new_labels_dir, train_images_dir, train_labels_dir)
    move_files(new_image_files[train_split_idx:test_split_idx], new_images_dir, new_labels_dir, test_images_dir, test_labels_dir)
    move_files(new_image_files[test_split_idx:], new_images_dir, new_labels_dir, val_images_dir, val_labels_dir)

    print("New data_old split and added to the dataset successfully.")

split_and_add_new_data(new_images_dir, new_labels_dir, train_ratio=0.8, test_ratio=0.1)
