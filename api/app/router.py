import os
import uuid

from fastapi import APIRouter, UploadFile, File, Cookie
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import status
from celery import Celery
from celery.result import AsyncResult

from app.contracts import YtDownloadRequest


VIDEOS_DIR = "videos"


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
    Process an uploaded image file and
    return the processed image as a Base64 string.

    Args:
        image (UploadFile): The uploaded image file.

    Returns:
        JSONResponse: A JSON response with a success message
        and the processed image as a Base64 string, or
        a JSON response with an error message
        if there is a server error during image processing.
    """
    img_binary = image.file.read()

    try:
        task = celery.send_task("image", args=(img_binary,))
        res_img_b64 = task.get()
    except:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"msg": "Server error while processing image", "result": None},
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"msg": "Image has been labeled successfully", "result": res_img_b64},
    )


@router.post("/video")
async def create_video_task(
    video_data: YtDownloadRequest, vid_label_task_id: str | None = Cookie(default="-1")
):
    """
    Create a video processing task.

    This endpoint is used to create a video processing task.
    It checks if there is an ongoing task with
    the same task ID and returns a conflict response if so.
    If there is no ongoing task, it generates a new task ID, sends
    a task to a Celery worker, and returns a success response with the task ID.

    Args:
        video_data (YtDownloadRequest): The request body containing
        the video data, including the path to the model dump.
        vid_label_task_id (str, optional): The task ID of the video
        labeling task. Passed as a cookie in the request. Defaults to "-1".

    Returns:
        JSONResponse: Success response with status code 201 and the new task ID.
        Conflict response with status code 409
        if there is an ongoing task with the same task ID.
    """
    res = AsyncResult(id=vid_label_task_id)
    if res.status in ["STARTED", "RETRY"]:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"msg": "Please wait until current task completes"},
        )
    else:
        res.forget()

    task_id = str(uuid.uuid4())

    celery.send_task("yt_video", kwargs=video_data.model_dump(), task_id=task_id)

    resp = JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"msg": "Task has been created successfully", "task_id": task_id},
    )
    resp.set_cookie(key="vid_label_task_id", value=task_id)
    return resp


@router.get("/status")
async def check_video_status(vid_label_task_id: str | None = Cookie(default="-1")):
    """
    Check the status of a video processing task.

    Args:
        vid_label_task_id (str, optional): The task ID of the video
        labeling task. Passed as a cookie in the request. Defaults to "-1".

    Returns:
        StreamingResponse or JSONResponse: A streaming response with
        the labeled video file if the task is completed successfully.
        A JSON response indicating the task status if the task is
        pending, in progress, or encountered an error.
    """

    def iterfile(file_path):
        with open(file_path, mode="rb") as file_like:
            yield from file_like

    res = AsyncResult(id=vid_label_task_id)

    if res.status == "SUCCESS":
        return StreamingResponse(
            content=iterfile(os.path.join(VIDEOS_DIR, "labeled_videos", res.result)),
            media_type="video/mp4",
        )
    elif res.status == "PENDING":
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"msg": "Please, start the task"},
        )
    elif res.status in ["STARTED", "RETRY"]:
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"msg": "Please wait, your video is being processed..."},
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"msg": "Oops... Something went wrong with your video"},
        )
