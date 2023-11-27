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
from torch import nn
import torch
from efficientnet_pytorch import EfficientNet
from torchvision import transforms
from tqdm import tqdm

import config


class EfficientNet_V2(nn.Module):
    def __init__(self, n_out):
        super(EfficientNet_V2, self).__init__()
        # Define model
        self.effnet = EfficientNet.from_pretrained(f"efficientnet-b0")
        self.internal_embedding_size = self.effnet._fc.in_features
        self.effnet._fc = nn.Linear(
            in_features=self.internal_embedding_size, out_features=n_out
        )

    def forward(self, x):
        return self.effnet(x)


celery = Celery(__name__)
celery.conf.broker_url = os.getenv("CELERY_BROKER_URL")
celery.conf.result_backend = os.getenv("CELERY_RESULT_BACKEND")

yolo_model = YOLO(
    model=os.path.join(config.WEIGHTS_DIR, os.getenv("YOLO_CHECKPOINT")), task="detect"
)
cls_model = EfficientNet_V2(n_out=85)
cls_model.load_state_dict(
    torch.load(
        os.path.join(config.WEIGHTS_DIR, os.getenv("CLS_CHECKPOINT")),
        map_location=torch.device("cpu"),
    )
)
cls_model.eval()


def get_image_class(image, bbox) -> int:
    crop = image[bbox[1] : bbox[3], bbox[0] : bbox[2]]
    data_transforms = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Resize((512, 512)),
        ]
    )
    image = data_transforms(crop)
    image = image.unsqueeze(0).float()

    output = cls_model(image)
    prediction = torch.argmax(output, 1).detach().cpu().numpy()[0]
    return config.CLS_LABELS[prediction]


def draw_predictions(image: np.ndarray):
    results = yolo_model.predict(image, stream=True, verbose=False)
    for result in results:
        boxes = result.boxes.cpu().numpy()
        for box in boxes:
            r = box.xyxy[0].astype(int)
            crop_cls = get_image_class(image, r)
            cv2.rectangle(image, r[:2], r[2:], (255, 0, 0), 3)

            (text_width, text_height) = cv2.getTextSize(
                crop_cls, cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, thickness=1
            )[0]
            text_offset_x = r[0]
            text_offset_y = r[1] - 5

            box_coords = (
                (text_offset_x, text_offset_y),
                (text_offset_x + text_width + 2, text_offset_y - text_height),
            )
            cv2.rectangle(
                image,
                box_coords[0],
                box_coords[1],
                color=(255, 255, 255),
                thickness=cv2.FILLED,
            )

            cv2.putText(
                image,
                crop_cls,
                (r[0], r[1] - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=1,
                color=(0, 0, 0),
                thickness=1,
            )

    return image


@celery.task(name="image", time_limit=10, soft_time_limit=5)
def process_image(img_binary: str):
    """
    Process an image by performing object detection using the YOLO model.

    Args:
        img_binary (str): A string representing the binary data of an image.

    Returns:
        str: A string representing the processed image in base64 format.
    """
    file_bytes = np.asarray(bytearray(img_binary), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # image = Image.open(BytesIO(img_binary))
    # image = np.array(image)

    image = Image.fromarray(cv2.cvtColor(draw_predictions(image), cv2.COLOR_BGR2RGB))

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
            config.YDL_CONFIG
            | {
                "outtmpl": os.path.join(
                    config.DOWNLOAD_VIDEO_DIR, f"{os.getpid()}.%(ext)s"
                )
            }
        ) as ydl:
            metainf = ydl.extract_info(yt_link, download=True)
    except Yt.DownloadError as exc:
        raise self.retry(exc=exc, countdown=5)

    video_path = os.path.join(
        config.DOWNLOAD_VIDEO_DIR, f"{metainf['id']}.{metainf['ext']}"
    )
    os.rename(
        src=os.path.join(config.DOWNLOAD_VIDEO_DIR, f"{os.getpid()}.{metainf['ext']}"),
        dst=video_path,
    )

    if time_intervals:
        # example:
        # ffmpeg -ss 00:00:01 -to 00:00:03 -i vid.mp4 -ss 00:00:05 -to 00:00:07 -i vid.mp4
        # -filter_complex "[0:v] [0:a] [1:v] [1:a] concat=n=2:v=1:a=1 [v] [a]"
        # -map "[v]" -map "[a]" output.mp4

        new_video_path = os.path.join(
            config.DOWNLOAD_VIDEO_DIR, f"{metainf['id']}_concat.{metainf['ext']}"
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
        config.DOWNLOAD_VIDEO_DIR, f"{metainf['id']}_lowfps.{metainf['ext']}"
    )
    ffmpeg_params = (
        ["ffmpeg"]
        + ["-i", old_video_path]
        + ["-vf"]
        + [f"setpts={target_fps}/FR*PTS"]
        #    \ [tmp] colorchannelmixer=0:0:1:0:0:1:0:0:1:0:0 [out]"]
        + ["-r", str(target_fps)]
        + [video_path]
    )
    subprocess.check_output(ffmpeg_params, timeout=300)
    os.remove(old_video_path)

    os.makedirs(config.LABELED_VIDEO_DIR, exist_ok=True)

    tmp_path = os.path.normpath(video_path)
    tmp_path = tmp_path.split(os.sep)[-1]
    res_vid = os.path.join(
        config.LABELED_VIDEO_DIR, f"{tmp_path[:tmp_path.rfind('.')]}.avi"
    )
    res_vid_mp4 = os.path.join(config.LABELED_VIDEO_DIR, tmp_path)

    # cv2 (and YOLO) gives .avi output with uncompressed video,
    # so we need to convert it to .mp4 with ffmpeg to reduce size
    capture = cv2.VideoCapture(video_path)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(
        res_vid,
        fourcc=fourcc,
        fps=target_fps,
        frameSize=(width, height),
    )

    for i in tqdm(range(0, frame_count)):
        capture.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = capture.read()

        if not ret:
            break

        out.write(draw_predictions(frame))

    capture.release()
    out.release()

    ffmpeg_params = ["ffmpeg"]
    ffmpeg_params += ["-i", res_vid]
    ffmpeg_params += ["-y", res_vid_mp4]
    subprocess.check_output(ffmpeg_params, timeout=300)

    os.remove(res_vid)
    os.remove(video_path)

    return tmp_path
