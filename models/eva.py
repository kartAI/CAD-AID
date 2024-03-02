import cv2
from ultralytics import YOLO
import numpy as np
from PIL import Image
from ultralytics.utils.ops import scale_image
import os
import matplotlib.pyplot as plt

def train_model(model):
    model.train(data='data/data.yaml', classes=[5], epochs=10)


def predict_seg (img, model):

    results = model(img, save=False, stream=True)

    return results

# Resize mask if output from model lower resolution
def resize_mask(results,img):
    h, w, _ = img.shape
    resized_masks = []

    for r in results:

        img_array = r.plot()
        im = Image.fromarray(img_array[..., :: -1])  # RGB image
        #im.show()

        masks = r.masks.data.numpy()
        for mask in masks:
            resized_mask = cv2.resize(mask, (w, h))
            resized_masks.append(resized_mask)
    return resized_masks

# Combine resized mask with original image
def overlay(img_mask, mask,color,alpha):
    color = color[::-1]
    colored_mask = np.expand_dims(mask, 0).repeat(3, axis=0)
    colored_mask = np.moveaxis(colored_mask, 0, -1)
    masked = np.ma.MaskedArray(img_mask, mask=colored_mask, fill_value=color)
    image_overlay = masked.filled()
    image_combined = cv2.addWeighted(img_mask, 1 - alpha, image_overlay, alpha, 0)

    return image_combined
def combine_img_masks(img,masks):
    img_with_mask = np.copy(img)
    for i in masks:
        img_with_mask = overlay(img_with_mask, i, color=(0, 255, 0), alpha=0.3)

    return img_with_mask

# Plot segmented image with resized masks
def plot_segmented_img(img_with_masks):
    cv2.imshow("r", img_with_masks)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Draw contours around each mask.Might not be used in future
def mask_contours(masks, image):
    all_contours = []
    for i, mask in enumerate(masks):
        mask = mask.astype(np.uint8)
        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        all_contours.extend(contours)

    return all_contours

def plot_contoured_masks(image,contours):
    for cnt in contours:
        cv2.drawContours(image, [cnt], 0, (0, 255, 0), 2)  # Draw contours in green with thickness 2
    cv2.imshow("contours", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    model = YOLO("../runs/segment/train14/weights/best.pt")

    img_path = "../data_seg_anylabeling/test/images/svart-hvit-2d-plantegning-med-mal.jpg"
    img = cv2.imread(img_path)

    # Get results from model
    segmentation_results=predict_seg(img, model)

    # Resize masks if output img from model has low resolution
    masks = resize_mask(segmentation_results,img)
    # Combine resized mask with original image
    masked_img = combine_img_masks(img, masks)
    #plot_segmented_img(masked_img)
