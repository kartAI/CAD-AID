import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv


from utils.detection_handler import DetectionHandler

def main():
    load_dotenv(".env.dev")

    run_detection = DetectionHandler()
    run_detection.check_and_execute()


if __name__ == "__main__":
    main()
    