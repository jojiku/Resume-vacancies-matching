import uvicorn
from fastapi import FastAPI

from app.router import router as router_dwnl


app = FastAPI(
    title="Road Sign Detector",
    description="This service can detect road signs on your \
    image or video with high speed and accuracy",
    version="0.0.1",
    docs_url="/docs",
    redoc_url=None,
)

app.include_router(router_dwnl)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
