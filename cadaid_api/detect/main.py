from fastapi import FastAPI
from src.api import app as detect_app

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Detect service is running"}

app.mount("/detect", detect_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)