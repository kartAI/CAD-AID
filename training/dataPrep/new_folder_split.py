import os
import shutil
import random

# Base directory (parent of the 'data_prep' directory)
base_dir = os.path.dirname(os.path.dirname(__file__))

# Training data directories
train_images_dir = os.path.join(base_dir, "data", "train", "images")
train_labels_dir = os.path.join(base_dir, "data", "train", "json_labels")

# Testing data directories
test_images_dir = os.path.join(base_dir, "data", "test", "images")
test_labels_dir = os.path.join(base_dir, "data", "test", "json_labels")

# Validation data directories
val_images_dir = os.path.join(base_dir, "data", "val", "images")
val_labels_dir = os.path.join(base_dir, "data", "val", "json_labels")

# New data directories
new_images_dir = os.path.join(base_dir, "images")
new_labels_dir = os.path.join(base_dir, "json_labels")

def split_and_add_new_data(new_images_dir, new_labels_dir, train_ratio=0.8, test_ratio=0.1):

    # List all new image files
    valid_ext = [".jpg", ".jpeg", ".png", ".JPG", ".PNG", ".JPEG"]
    new_image_files = [f for f in os.listdir(new_images_dir) if os.path.splitext(f)[1] in valid_ext]
    random.shuffle(new_image_files)

    # Calculate split indices
    total_new_images = len(new_image_files)
    train_split_idx = int(total_new_images * train_ratio)
    test_split_idx = train_split_idx + int(total_new_images * test_ratio)

    def move_files(files, src_img_dir, src_lbl_dir, dest_img_dir, dest_lbl_dir):
        for f in files:
            src_img_path = os.path.join(src_img_dir, f)
            dest_img_path = os.path.join(dest_img_dir, f)
            src_lbl_path = os.path.join(src_lbl_dir, f.replace(os.path.splitext(f)[1], ".txt"))
            dest_lbl_path = os.path.join(dest_lbl_dir, f.replace(os.path.splitext(f)[1], ".txt"))

            if os.path.exists(src_img_path) and os.path.exists(src_lbl_path):
                print("Moving", src_img_path, "to", dest_img_path)
                print("Moving", src_lbl_path, "to", dest_lbl_path)

                shutil.move(src_img_path, dest_img_path)
                shutil.move(src_lbl_path, dest_lbl_path)
            else:
                print("File not found:", src_img_path, "or", src_lbl_path)

    # Split and move new images and json_labels
    move_files(new_image_files[:train_split_idx], new_images_dir, new_labels_dir, train_images_dir, train_labels_dir)
    move_files(new_image_files[train_split_idx:test_split_idx], new_images_dir, new_labels_dir, test_images_dir, test_labels_dir)
    move_files(new_image_files[test_split_idx:], new_images_dir, new_labels_dir, val_images_dir, val_labels_dir)

    print("New data split and added to the dataset successfully.")

split_and_add_new_data(new_images_dir, new_labels_dir, train_ratio=0.8, test_ratio=0.1)
