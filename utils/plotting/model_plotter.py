import cv2
import numpy as np
from PIL import Image
from ultralytics.utils.plotting import Annotator, colors

class ModelPlotter:
    def __init__(self, model_instance):
        self.model_instance = model_instance

        
      
        self.image_path = getattr(model_instance, 'prediction_image', None)

    def visualize_predictions(self, results):
        for r in results:
            img_array = r.plot()
            img = Image.fromarray(img_array[..., :: -1])
            img.show()

    def plot_pretty_segments(self, model, conf):
        
        img = cv2.imread(self.image_path)
        results = model.track(img, persist=False, conf=conf)

        # Class names
        names = model.model.names

        annotator = Annotator(img, line_width=3)

        # Empty image array
        mask_img = np.zeros_like(img)

        for r in results:
            if r.masks is not None:
                # Normalize mask coordinates to fill polygons
                masks_norm = r.masks.xyn

                # Mask coordinates to use in annotator
                masks = r.masks.xy
                track_ids = r.boxes.id.int().cpu().tolist()
                clss = r.boxes.cls.tolist()
                confidence = r.boxes.conf.tolist()

                for mask, track_id, cls, conf_score in zip(masks_norm, track_ids, clss, confidence):
                    mask_color = colors(track_id, True)
                    polygon = np.array([[(x * img.shape[1], y * img.shape[0]) for x, y in mask]], dtype=np.int32)

                    # Fill the polygon in the mask_img
                    cv2.fillPoly(mask_img, polygon, mask_color)

                for mask, track_id, cls, conf_score in zip(masks, track_ids, clss, confidence):
                    mask_color = colors(track_id, True)
                    label = f'{names[int(cls)]}: {conf_score:.2f}'
                    annotator.seg_bbox(mask=mask, mask_color=mask_color, label=label)

        alpha = 0.3
        # Blend filled mask with original image
        blended_img = cv2.addWeighted(img, 0.7, mask_img, alpha, 0)

        cv2.imshow("results", blended_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        return blended_img