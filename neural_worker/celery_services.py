import os
import base64
from io import BytesIO
import subprocess

from PIL import Image
from celery import Celery
from ultralytics import YOLO
import cv2
import numpy as np
import yt_dlp as Yt


YOLO_WEIGHTS_DIR = "yolo_weights"

YDL_CONFIG = {
    "quiet": True,
    "no-warnings": False,
    "ignore-errors": False,
    "no-overwrites": True,
    "format": "best",
    "keepvideo": True,
}
DOWNLOAD_VIDEO_DIR = "example_images/download_videos"
LABELED_VIDEO_DIR = "example_images/labeled_videos"


celery = Celery(__name__)
celery.conf.broker_url = os.getenv("CELERY_BROKER_URL")
celery.conf.result_backend = os.getenv("CELERY_RESULT_BACKEND")

yolo_model = YOLO(
    model=os.path.join(YOLO_WEIGHTS_DIR, os.getenv("YOLO_CHECKPOINT")), task="detect"
)


@celery.task(name="image", time_limit=10, soft_time_limit=5)
def process_image(img_binary: str):
    """
    Process an image by performing object detection using the YOLO model.

    Args:
        img_binary (str): A string representing the binary data of an image.

    Returns:
        str: A string representing the processed image in base64 format.
    """
    image = Image.open(BytesIO(img_binary))
    image = np.array(image)

    results = yolo_model.predict(image, stream=True)
    for result in results:
        boxes = result.boxes.cpu().numpy()
        for box in boxes:
            r = box.xyxy[0].astype(int)
            cv2.rectangle(image, r[:2], r[2:], (255, 0, 0), 3)

    image = Image.fromarray(image)

    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()

    return img_b64


@celery.task(
    bind=True, name="yt_video", time_limit=600, soft_time_limit=540, track_started=True
)
def process_video(self, yt_link: str, time_intervals: list, target_fps: int):
    """
    Process a YouTube video by downloading it,
    extracting specified time intervals, reducing the fps,
    applying object detection, and converting the output video to mp4.

    Args:
        yt_link (str): The YouTube video link.
        time_intervals (list): A list of tuples representing the start and end times
        of the desired intervals in the format "%H:%M:%S".
        target_fps (int): The desired frames per second for the output video.

    Returns:
        str: The path to the labeled video in .mp4 format.
    """
    try:
        with Yt.YoutubeDL(
            YDL_CONFIG
            | {"outtmpl": os.path.join(DOWNLOAD_VIDEO_DIR, f"{os.getpid()}.%(ext)s")}
        ) as ydl:
            metainf = ydl.extract_info(yt_link, download=True)
    except Yt.DownloadError as exc:
        raise self.retry(exc=exc, countdown=5)

    video_path = os.path.join(DOWNLOAD_VIDEO_DIR, f"{metainf['id']}.{metainf['ext']}")
    os.rename(
        src=os.path.join(DOWNLOAD_VIDEO_DIR, f"{os.getpid()}.{metainf['ext']}"),
        dst=video_path,
    )

    if time_intervals:
        # example:
        # ffmpeg -ss 00:00:01 -to 00:00:03 -i vid.mp4 -ss 00:00:05 -to 00:00:07 -i vid.mp4
        # -filter_complex "[0:v] [0:a] [1:v] [1:a] concat=n=2:v=1:a=1 [v] [a]"
        # -map "[v]" -map "[a]" output.mp4

        new_video_path = os.path.join(
            DOWNLOAD_VIDEO_DIR, f"{metainf['id']}_concat.{metainf['ext']}"
        )
        ffmpeg_params = ["ffmpeg"]

        for pair in time_intervals:
            ffmpeg_params += ["-ss", pair[0]] + ["-to", pair[1]] + ["-i", video_path]

        ffmpeg_params += [
            "-filter_complex",
            f'{" ".join([f"[{idx}:v] [{idx}:a]" for idx in range(len(time_intervals))])} \
            concat=n={len(time_intervals)}:v=1:a=1 [v] [a]',
        ]

        ffmpeg_params += ["-map"] + ["[v]"] + ["-map"] + ["[a]"]
        ffmpeg_params += ["-y"] + [new_video_path]

        subprocess.check_output(ffmpeg_params, timeout=300)

        os.remove(video_path)  # can be removed for 'cache'
        video_path = new_video_path

    old_video_path = video_path
    video_path = os.path.join(
        DOWNLOAD_VIDEO_DIR, f"{metainf['id']}_lowfps.{metainf['ext']}"
    )
    ffmpeg_params = (
        ["ffmpeg"]
        + ["-i", old_video_path]
        + ["-vf", f"setpts={target_fps}/FR*PTS"]
        + ["-r", str(target_fps)]
        + [video_path]
    )
    subprocess.check_output(ffmpeg_params, timeout=300)
    os.remove(old_video_path)

    yolo_model.predict(
        video_path,
        show_labels=False,
        show_conf=False,
        save=True,
        project=LABELED_VIDEO_DIR.split("/")[0],
        name=LABELED_VIDEO_DIR.split("/")[1],
        exist_ok=True,
    )

    # YOLO gives .avi output with uncompressed video,
    # so we need to convert it to .mp4 to reduce size
    tmp_path = os.path.normpath(video_path)
    tmp_path = tmp_path.split(os.sep)[-1]
    res_vid = os.path.join(LABELED_VIDEO_DIR, f"{tmp_path[:tmp_path.rfind('.')]}.avi")
    res_vid_mp4 = os.path.join(LABELED_VIDEO_DIR, tmp_path)

    ffmpeg_params = ["ffmpeg"]
    ffmpeg_params += ["-i", res_vid]
    ffmpeg_params += ["-y", res_vid_mp4]
    subprocess.check_output(ffmpeg_params, timeout=300)

    os.remove(res_vid)
    os.remove(video_path)

    return tmp_path
