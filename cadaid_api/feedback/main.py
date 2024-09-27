from fastapi import FastAPI
from src.api import app as feedback_app

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Feedback service is running"}

app.mount("/feedback", feedback_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)