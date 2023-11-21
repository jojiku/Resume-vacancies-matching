from io import BytesIO
import requests
import base64
import re

from PIL import Image
import streamlit as st


# interact with FastAPI endpoint
IMAGE_PROCESSING_URL = "http://api:8000/image"
VIDEO_PROCESSING_URL = "http://api:8000/video"
VIDEO_STATUS_URL = "http://api:8000/status"


def process(image: str):
    files = {
        "image": image.getvalue(),
    }

    r = requests.post(IMAGE_PROCESSING_URL, files=files)

    return r.json()["result"]


# construct UI layout
st.title(":violet[ITMO] PDL RoadSign Detection Project")

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
        with st.spinner("Sending request to API..."):
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
yt_link = st.text_input(
    "Enter your YouTube video link",
    placeholder="youtube.com/watch?v=dQw4w9WgXcQ",
)
fps = st.text_input(
    "Enter desired video FPS",
    placeholder="10",
)

if "num_features" not in st.session_state:
    st.session_state.num_features = 0
features_list = []

ts_ba, ts_br = st.columns(2)

if ts_ba.button("Add timestamp"):
    st.session_state.num_features += 1

if ts_br.button("Remove timestamp"):
    if st.session_state.num_features > 0:
        st.session_state.num_features -= 1

for i in range(st.session_state.num_features):
    feature = st.text_input(
        f"Enter timestamp", placeholder="00:03:45-00:04:15", key=f"new_feature_{i}"
    )
    features_list.append(feature)

if "s" not in st.session_state:
    st.session_state.s = requests.Session()

if st.button("Upload video"):
    for idx, ts in enumerate(features_list):
        m = re.fullmatch(r"\d+[:]\d+[:]\d+[-]\d+[:]\d+[:]\d+", ts)
        if not m:
            raise ValueError(f"Timestamp {ts} not in %H:%M:%S format")

        s, t = ts.split("-")
        features_list[idx] = [s, t]

    with st.spinner("Sending request to API..."):
        r = st.session_state.s.post(
            url=VIDEO_PROCESSING_URL,
            json={
                "yt_link": yt_link,
                "time_intervals": features_list,
                "target_fps": int(fps) if fps else 10,
            },
        )

    st.text(r.json()["msg"])

if st.button("Check status"):
    with st.spinner("Sending request to API..."):
        r = st.session_state.s.get(url=VIDEO_STATUS_URL)

    if r.status_code == 200:
        st.video(r.content)
    else:
        st.text(r.json()["msg"])
