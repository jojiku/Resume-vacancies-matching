import os
import base64
from io import BytesIO

from PIL import Image
from celery import Celery
from ultralytics import YOLO
import cv2
import numpy as np


YOLO_WEIGHTS_DIR = "yolo_weights"


celery = Celery(__name__)
celery.conf.broker_url = os.getenv("CELERY_BROKER_URL")
celery.conf.result_backend = os.getenv("CELERY_RESULT_BACKEND")

yolo_model = YOLO(os.path.join(YOLO_WEIGHTS_DIR, os.getenv("YOLO_CHECKPOINT")))


@celery.task(name="image")
def process_image(img_binary: str):
    """ """
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


@celery.task(name="yt_video")
def process_video(yt_link: str):
    pass
