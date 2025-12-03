from typing import Union
import io
from PIL import Image
from fastapi import FastAPI, File, UploadFile, Query
from fastapi.responses import JSONResponse
from src.run_detection import predict_drawings

app = FastAPI()


@app.post("/detect")
async def detect(image: UploadFile = File(...),  conf: float = Query(0.25, ge=0.0, le=1.0, description="Confidence threshold for detections")):
    contents = await image.read()
    image = Image.open(io.BytesIO(contents))
    predictions = predict_drawings(image, conf)
    return JSONResponse(content={"predictions": predictions})

