import shutil
import os

import uvicorn
from fastapi import FastAPI

from app.router import router as router_dwnl, VIDEOS_DIR


def remove_old_static(_: FastAPI):
    for root, dirs, files in os.walk(VIDEOS_DIR):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))

    yield


app = FastAPI(
    title="Road Sign Detector",
    description="This service can detect road signs on your \
    image or video with high speed and accuracy",
    version="0.0.1",
    docs_url="/docs",
    redoc_url=None,
    lifespan=remove_old_static,
)

app.include_router(router_dwnl)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
