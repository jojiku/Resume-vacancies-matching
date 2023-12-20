import streamlit as st


st.set_page_config(
    page_title="SidePage",
    page_icon="👋",
)


st.snow()

# construct UI layout
st.title(":violet[ITMO] PDL Resume&Vacancies Project")

st.header(
    "This R&V service seamlessly matches suitable job listings to \
    resumes and vice versa, streamlining the job search process \
    for both employers and job seekers. \
    This streamlit frontend uses a FastAPI service as backend. \
    Visit this URL at `/docs` for FastAPI documentation."
)

st.image("static/meme.png")
st.image("static/prec.jpg")

st.sidebar.success("Choose your side wisely!")

st.divider()
