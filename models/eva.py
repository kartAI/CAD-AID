import cv2
from ultralytics import YOLO
import numpy as np
from PIL import Image
from ultralytics.utils.ops import scale_image
import os
import matplotlib.pyplot as plt
import cv2
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors


def predict_seg (img, model):
    results = model(img, save=False, conf=0.4)

    for r in results:

        img_array = r.plot()
        img = Image.fromarray(img_array[..., :: -1])  # RGB image
        img.show()

    return results

# ------- RESIZE MASKS ----------------------------
# Resize mask if output from model lower resolution
def resize_mask(img,seg_res):
    h, w, _ = img.shape
    resized_masks = []

    for r in seg_res:
        seg_masks = r.masks.data.numpy()
        for mask in seg_masks:
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


# ------------ BARE LITT ROT :) ---------------------
def plot_seg_with_tracking(img, model):
    results = model.track(img, persist=True)
    names = model.model.names
    annonator = Annotator(img, line_width=3)
    for r in results:
        if r.masks is not None:
            masks = r.masks.xy

            track_ids = r.boxes.id.int().cpu().tolist()
            clss = r.boxes.cls.data.numpy()

            for mask, track_id, cls in zip(masks, track_ids, clss):
                annonator.seg_bbox(mask=mask, mask_color=colors(track_id, True), det_label=names[int(cls)])
    cv2.imshow("results", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def plot_contoured_masks(img,model):
    results = model(img, save=False)
    names = model.model.names
    annonator = Annotator(img, line_width=2)
    for r in results:
        if r.masks is not None:
            clss = r.boxes.cls.data.numpy()
            masks = r.masks.xy
            for mask, cls in zip(masks, clss):
                annonator.seg_bbox(mask=mask, mask_color=colors(int(cls), True), det_label=names[int(cls)])
    cv2.imshow("results", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    model = YOLO("../runs/segment/train14/weights/best.pt")

    img_path = "../data_seg/test/images/svart-hvit-2d-plantegning-med-mal.jpg"
    img = cv2.imread(img_path)

    # Get results from model
    seg_results=predict_seg(img, model)


    # Resize masks if output img from model has low resolution
    #img_copy = img.copy()
    #masks = resize_mask(img_copy,seg_results)
    # Combine resized mask with original image
    #masked_img = combine_img_masks(img_copy, masks)
    #plot_segmented_img(masked_img)
