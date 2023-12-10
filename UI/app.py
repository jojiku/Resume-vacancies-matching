import streamlit as st

import PyPDF2
from gensim.models import Doc2Vec
from numpy.linalg import norm
import pandas as pd
import numpy as np
import fitz 
import hydralit_components as hc
 
model = Doc2Vec.load('C:/Users/Tseh/resume_matching/cv_job_maching_best.model')

def calculate_similarity_new(resume, vacancy):
    v1 = model.infer_vector(resume.split())
    v2 = model.infer_vector(vacancy.split())
    similarity = 100 * (np.dot(np.array(v1), np.array(v2))) / (norm(np.array(v1)) * norm(np.array(v2)))
    return round(similarity, 2)


# Streamlit app
def main():
    st.write("""
    # Resume - job matching
    
    ## Just upload your resume in pdf to get your dream job! 
    """)

    st.sidebar.header('Your file to upload:')
    uploaded_file = st.sidebar.file_uploader("Upload your resume in pdf", type="pdf")

    if uploaded_file is not None:
        pdf = PyPDF2.PdfReader(uploaded_file)
        resume = ""
        for i in range(len(pdf.pages)):
            pageObj = pdf.pages[i]
            resume += pageObj.extract_text()

        st.subheader("Uploaded PDF Content:")

        pdf_document = fitz.open(uploaded_file)
        for page in pdf_document:
            image_bytes = page.get_pixmap().tobytes()
            st.image(image_bytes)


        resume_text = st.text_area("Enter your resume text:", " ")

        tested = pd.read_csv('C:/Users/Tseh/resume_matching/results.csv')
        
        if st.button('Find Matching Jobs'):
            with hc.HyLoader('Looking through our databases...', hc.Loaders.standard_loaders, index=[5]):
                tested['similarity'] = tested['vacancy'].apply(lambda x: calculate_similarity_new(resume_text, x))
            
            tested = tested.drop(columns = ['resume', 'similarity_score'])
            tested = (tested.sort_values(by='similarity', ascending=False)).head(10)

            st.subheader("Top 10 vacancies for your resume:")
            st.dataframe(tested)

if __name__ == '__main__':
    main()