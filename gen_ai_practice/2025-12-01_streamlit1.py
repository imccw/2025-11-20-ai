import os, base64
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY")
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant that can describe images."),
        (
            "human",
            [
                {"type": "text", "text": "{input}"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/jpeg;base64,{image}",
                        "detail": "low",
                    },
                },
            ],
        ),
    ]
)

chain = prompt | llm

def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode()

st.title("Image Analysis Using Gemini")
col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Upload your image", type=["jpg", "png"])

with col2:
    if uploaded_file:
        st.image(uploaded_file)
    else:
        st.write("Image Preview")

question = st.text_input("Enter a question")

if question and uploaded_file:
    image = encode_image(uploaded_file)
    res = chain.invoke({"input": question, "image": image})
    st.write(res.content)
