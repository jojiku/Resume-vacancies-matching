import requests

import streamlit as st
import pandas as pd


st.set_page_config(
    page_title="HR Page",
    page_icon="👧",
)

# interact with FastAPI endpoint
SEARCH_URL = "http://api:5041/search_res"
UPDATE_URL = "http://api:5041/update_vac"
MAX_CHARS = 1000

# st.snow()

# construct UI layout
st.title(":violet[HR] R&V page")

st.header(
    "This page is intended for people, who is in search of \
    the best worker. You can write your job description \
    (to every minor detail) and search corresponding \
    worker!"
)

st.divider()

st.subheader("Use text field below to search corresponding worker!")
resume = st.text_area("Your job description", height=100)

if st.button("Get resumes"):
    if resume:
        with st.spinner("Sending request to API..."):
            data = requests.get(url=f"{SEARCH_URL}", params={"text": resume}).json()
            df = pd.DataFrame(data)

        st.subheader("Top 10 resumes for your job:")
        st.dataframe(df.style.highlight_max(axis=0), height=300)

        st.markdown("---")

        st.title("Resumes cards:")
        for index, row in df.iterrows():
            st.markdown(
                f"""
                <div style="border: 1px solid #e6e6e6; border-radius: 10px; padding: 15px;
                  margin-bottom: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
                    <h3 style="color: #1f4096;">{row['job_title']}</h3>
                    <p style="color: #555;">Experience: {row['experience']}</p>
                    <p style="color: #555;">
                    Gender, age: {row['gend_age'] 
                                    if row['gend_age'] else "Not provided"}</p>
                    <p style="color: #555;">
                    Education: {row['edu'] 
                                    if row['edu'] else "Not provided"}</p>
                    <p style="color: #555;">
                    Salary: {row['salary'] 
                                    if row['salary'] else "Not provided"}</p>
                    <p style="color: #555;">
                    Last updated at: {row['upd_date'] 
                                    if row['upd_date'] else "Not provided"}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:
        st.write("Write your resume!")

st.divider()

st.subheader("Use text fields below to add job vacancy!")

st.write("**Required fields**")
employer = st.text_input("The name of the employer", max_chars=100)
descr = st.text_area(
    "The description of the job (to every minor detail)", max_chars=2000, height=300
)
key_req = st.text_input("The key requirements for the job", max_chars=500)
spec = st.text_input("The specialization of the job", max_chars=500)
req_exp = st.text_input("The experience required for the job", max_chars=100)

st.write("**Optional fields**")

vac_title = st.text_input("The title of the vacancy", max_chars=MAX_CHARS)
sal_from = st.text_input("The starting salary", max_chars=MAX_CHARS)
sal_to = st.text_input("The ending salary", max_chars=MAX_CHARS)
sch_type = st.text_input(
    "The job schedule type (e.g., office, remote)", max_chars=MAX_CHARS
)
schedule = st.text_input("Desired Schedule (Full Day...)", max_chars=MAX_CHARS)
keywords = st.text_input("The keywords related to the job", max_chars=MAX_CHARS)
area = st.text_input("The location of the employer", max_chars=MAX_CHARS)
tags = st.text_input("The tags associated with the job", max_chars=MAX_CHARS)
publ_date = st.text_input("The date of job publishing", max_chars=MAX_CHARS)

if st.button("Upload vacancy"):
    if all(el for el in [employer, descr, key_req, spec, req_exp]):
        with st.spinner("Sending request to API..."):
            resp = requests.post(
                url=f"{UPDATE_URL}",
                json={
                    "vac_title": vac_title,
                    "sal_from": sal_from,
                    "sal_to": sal_to,
                    "sch_type": sch_type,
                    "schedule": schedule,
                    "keywords": keywords,
                    "area": area,
                    "publ_date": publ_date,
                    "tags": tags,
                    "employer": employer,
                    "descr": descr,
                    "key_req": key_req,
                    "spec": spec,
                    "req_exp": req_exp,
                },
            ).json()

            if resp.get("success"):
                st.success("You vacancy has been added successfully!")

            else:
                st.write(resp["detail"])

    else:
        st.write("Fill at least required fields")

st.divider()

st.sidebar.success("This is HR page!")
