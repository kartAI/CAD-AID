import pytesseract
from pytesseract import Output
from PIL import Image

import easyocr

reader = easyocr.Reader(['en'])
extract_info = reader.readtext("data/test/images/fasade43.jpg")

for el in extract_info:
   print(el)