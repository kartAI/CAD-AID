from fastapi import FastAPI
from app.classification.routes import router as classification_router
from app.floorplan.routes import router as floorplan_router


app = FastAPI()
app.include_router(classification_router, prefix="/classification", tags=["classification"])
app.include_router(floorplan_router, prefix="/floorplan", tags=["floorplan"])




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)