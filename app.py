# Import necessary libraries  
import streamlit as st
import time
from qa_system import initialize_qa_system

st.title("PDF Chatbot")

# File uploader
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    # Save the uploaded file temporarily
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Initialize QA system
    with st.spinner("Initializing QA system..."):
        qa_system = initialize_qa_system("temp.pdf")
    
    st.success("QA system initialized successfully!")

    # Chat interface
    st.subheader("Chat with your PDF")
    user_question = st.text_input("Ask a question about your PDF:")

    if user_question:
        with st.spinner("Generating answer..."):
            start_time = time.time()
            result = qa_system.invoke({"query": user_question})
            end_time = time.time()

        st.write("Answer:", result['result'])
        st.write(f"Time taken to generate answer: {end_time - start_time:.2f} seconds")

    # Display chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if user_question:
        st.session_state.chat_history.append(("You", user_question))
        st.session_state.chat_history.append(("Bot", result['result']))

    st.subheader("Chat History")
    for role, message in st.session_state.chat_history:
        st.write(f"{role}: {message}")
else:
    st.write("Please upload a PDF file to start chatting.")