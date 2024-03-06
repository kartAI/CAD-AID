import cv2
from ultralytics import YOLO
import numpy as np
from PIL import Image
from ultralytics.utils.ops import scale_image
import os
import matplotlib.pyplot as plt
import cv2
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors, plot_results


def predict_seg (img, model):
    results = model(img, save=False, conf=0.4)

    for r in results:

        img_array = r.plot()
        img = Image.fromarray(img_array[..., :: -1])  # RGB image
        img.show()

    return results


# Pretty segmentations
def plot_seg_with_tracking(img, model):
    results = model.track(img, persist=False,conf=0.4)

    # Class names
    names = model.model.names

    annonator = Annotator(img, line_width=3)

    # empty image array
    mask_img = np.zeros_like(img)


    for r in results:
        if r.masks is not None:
            # Nrmalize mask coordinates to fill polygons
            masks_norm = r.masks.xyn

            # Mask coordinates to use in annotator
            masks = r.masks.xy


            track_ids = r.boxes.id.int().cpu().tolist()
            clss = r.boxes.cls.tolist()

            for mask, track_id, cls in zip(masks_norm, track_ids, clss):
                mask_color = colors(track_id,True)
                polygon = np.array([[(x * img.shape[1], y * img.shape[0]) for x, y in mask]], dtype=np.int32)

                # Fill the polygon in the mask_img
                cv2.fillPoly(mask_img, polygon, mask_color)

            for mask, track_id, cls in zip(masks, track_ids, clss):
                mask_color = colors(track_id,True)
                annonator.seg_bbox(mask=mask, mask_color=mask_color, det_label=names[int(cls)])


    alpha = 0.3
    # Blend filled mask with original image
    blended_img = cv2.addWeighted(img,0.7,mask_img,alpha,0)

    cv2.imshow("results", blended_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return results, blended_img

# Plot contours
def plot_contoured_masks(img,model):

    results = model(img, save=False)

    names = model.model.names
    annonator = Annotator(img, line_width=2)
    for r in results:
        if r.masks is not None:
            clss = r.boxes.cls.tolist()
            masks = r.masks.xy

            for mask, cls in zip(masks, clss):

                annonator.seg_bbox(mask=mask, mask_color=colors(int(cls), True), det_label=names[int(cls)])

    cv2.imshow("results", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    model = YOLO("../runs/segment/train15/weights/best.pt")
    #plot_results('../runs/segment', segment=True)

    img_path = "../data_seg/test/images/plantegning6_page_1.jpg"
    img = cv2.imread(img_path)

    # Get results from model
    #seg_results=predict_seg(img, model)
    #plot_contoured_masks(img,model)
    results, blended_img= plot_seg_with_tracking(img, model)


    # Resize masks if output img from model has low resolution
    #img_copy = img.copy()
    #masks = resize_mask(img_copy,seg_results)
    # Combine resized mask with original image
    #masked_img = combine_img_masks(img_copy, masks)
    #plot_segmented_img(masked_img)
