import requests

import streamlit as st
import pandas as pd


st.set_page_config(
    page_title="JSeeker Page",
    page_icon="💼",
)

# interact with FastAPI endpoint
SEARCH_URL = "http://api:5041/search_vac"
UPDATE_URL = "http://api:5041/update_res"

# st.snow()

# construct UI layout
st.title(":violet[Job Seeker] R&V page")

st.header(
    "This page is intended for people, who is in search of \
    the job of their life. You can write your resume \
    (to every minor detail) and search corresponding \
    vacancy!"
)

st.divider()

st.subheader("Use text field below to search corresponding vacancies!")
resume = st.text_area("Your resume", height=100)

if st.button("Get vacancies"):
    if resume:
        with st.spinner("Sending request to API..."):
            data = requests.get(url=f"{SEARCH_URL}", params={"text": resume}).json()
            df = pd.DataFrame(data)

        st.subheader("Top 10 vacancies for your resume:")
        st.dataframe(df.style.highlight_max(axis=0), height=300)

        st.markdown("---")

        st.title("Vacancies cards:")
        for index, row in df.iterrows():
            st.markdown(
                f"""
                <div style="border: 1px solid #e6e6e6; border-radius: 10px; padding: 15px;
                  margin-bottom: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
                    <h3 style="color: #1f4096;">{row['employer']}</h3>
                    <p style="color: #555;">Description: {row['descr']}</p>
                    <p style="color: #555;">
                    Salary (from): {row['sal_from'] 
                                    if row['sal_from'] else "Not provided"}</p>
                    <p style="color: #555;">
                    Salary (to): {row['sal_to'] 
                                    if row['sal_to'] else "Not provided"}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:
        st.write("Write your resume!")

st.divider()

st.subheader("Use text fields below to add your resume!")

st.write("**Required fields**")
job_title = st.text_input(
    "Job title you are looking for ('Android-developer...')", max_chars=30
)
experience = st.text_area(
    "Your working experience (to every minor detail)", max_chars=2000, height=300
)
edu = st.text_input("Your education", max_chars=100)

st.write("**Optional fields**")

gend_age = st.text_input("Gender and Age", max_chars=1000)
salary = st.text_input("Desired Salary", max_chars=1000)
city = st.text_input(
    "City of Residence and Readiness for Business Trips", max_chars=1000
)
employment = st.text_input("Desired Employment (Full, Partly...)", max_chars=1000)
schedule = st.text_input("Desired Schedule (Full Day...)", max_chars=1000)
last_wp = st.text_input("Last Employer", max_chars=1000)
last_jt = st.text_input("Last Job Title", max_chars=1000)
upd_date = st.text_input("Last Resume Update", max_chars=1000)
auto = st.text_input("Owns a Car", max_chars=1000)

if st.button("Upload resume"):
    if job_title and experience and edu:
        with st.spinner("Sending request to API..."):
            resp = requests.post(
                url=f"{UPDATE_URL}",
                json={
                    "gend_age": gend_age,
                    "salary": salary,
                    "city": city,
                    "employment": employment,
                    "schedule": schedule,
                    "last_wp": last_wp,
                    "last_jt": last_jt,
                    "upd_date": upd_date,
                    "auto": auto,
                    "job_title": job_title,
                    "experience": experience,
                    "edu": edu,
                },
            ).json()

            if resp.get("success"):
                st.success("You resume has been added successfully!")

            else:
                st.write(resp["detail"])

    else:
        st.write("Fill at least required fields")

st.divider()

st.sidebar.success("This is Job Seeker page!")
