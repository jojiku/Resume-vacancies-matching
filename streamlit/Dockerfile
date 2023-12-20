FROM python:3.11

COPY requirements.txt .
RUN pip install -r requirements.txt

ARG PROJECT=streamlit
ARG PROJECT_DIR=/${PROJECT}
RUN mkdir -p $PROJECT_DIR
WORKDIR $PROJECT_DIR
