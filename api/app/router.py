import os
import uuid

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi import status
from celery import Celery

# from app.contracts import DownloadingRequest


celery = Celery(__name__)
celery.conf.broker_url = os.getenv("CELERY_BROKER_URL")
celery.conf.result_backend = os.getenv("CELERY_RESULT_BACKEND")

router = APIRouter(tags=["tasker"])


@router.get("/")
def hello_world():
    """
    Hello world endpoint
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"msg": "Hello, world!"},
    )


@router.post("/image")
def create_image_task(image: UploadFile = File()):
    """
    Handles a POST request to the "/image" endpoint.
    Creates a task to process an image with YOLO using Celery.

    Args:
        image (UploadFile): An image to be processed with YOLO

    Returns:
        JSONResponse:
    """
    img_binary = image.file.read()

    task = celery.send_task("image", args=(img_binary,))
    res_img_b64 = task.get()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"result": res_img_b64},
    )


@router.post("/video")
async def create_video_task(yt_link: str):
    """
    Handles a POST request to the "/video" endpoint.
    Creates a task to downalod and process YouTube video
    with YOLO using Celery.

    Args:
        yt_link (str): YouTube video link

    Returns:
        JSONResponse:
    """
    task_id = uuid.uuid4()

    celery.send_task("yt_video", args=(yt_link,), task_id=task_id)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"msg": "Task has been created successfully", "task_id": task_id},
    )
