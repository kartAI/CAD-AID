import sys
import os
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv


from utils.detection_handler import DetectionHandler
from utils.text_manager import TextDetection

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    load_dotenv(".env.dev")

    run_detection = DetectionHandler()
    detected_text = run_detection.check_and_execute()

    # Output detected text for debugging
    logging.info(f"Detected text: {detected_text}")

if __name__ == "__main__":
    main()
    