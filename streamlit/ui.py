from io import BytesIO
import requests
import base64

from PIL import Image
import streamlit as st


# interact with FastAPI endpoint
IMAGE_PROCESSING_URL = "http://api:8000/image"


def process(image: str):
    files = {
        "image": image.getvalue(),
    }

    r = requests.post(IMAGE_PROCESSING_URL, files=files)

    print(r.status_code)
    print(r.json())

    return r.json()["result"]


# construct UI layout
st.title("ITMO PDL RoadSign Detection Project")

st.header(
    "Obtain labeled road signs on your image or any YouTube \
    video via YOLO implemented by Ultralytics. \
    This streamlit frontend uses a FastAPI service as backend. \
    Visit this URL at `:8000/docs` for FastAPI documentation."
)

st.divider()

st.subheader("Use button below to upload and process your image with road signs!")
input_image = st.file_uploader("insert image")

if st.button("Get road signs segmentation"):
    col1, col2 = st.columns(2)

    if input_image:
        labeled_img = process(input_image)
        original_image = Image.open(input_image).convert("RGB")

        segmented_image = Image.open(BytesIO(base64.b64decode(labeled_img)))
        col1.header("Original")
        col1.image(original_image, use_column_width=True)
        col2.header("Labeled")
        col2.image(segmented_image, use_column_width=True)

    else:
        # handle case with no image
        st.write("Insert an image!")

st.divider()

st.subheader("Use text field below to wite YouTube video link to be labeled!")
