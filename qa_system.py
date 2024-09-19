# Import necessary libraries
import re
import time
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from langchain.llms import HuggingFacePipeline
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings import CacheBackedEmbeddings, HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.storage import LocalFileStore
from langchain.chains import RetrievalQA
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import FlashrankRerank

# Function to clean the text
def clean_text(text):
    text = text.replace('\t', ' ')
    text = re.sub(' +', ' ', text)
    text = re.sub('\n+', '\n', text)
    text = re.sub(r'[^A-Za-z0-9\s,.]', '', text)
    return text

# Function to initialize the QA system
def initialize_qa_system(pdf_path):
    # Load and process the PDF
    loader = PyPDFLoader(pdf_path)
    pages = loader.load_and_split()
    cleaned_pages = [clean_text(page.page_content) for page in pages]

    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        is_separator_regex=False,
    )
    texts = text_splitter.create_documents(cleaned_pages)

    # Set up embeddings and vector store
    store = LocalFileStore("./cache/")
    embed_model_id = 'sentence-transformers/all-mpnet-base-v2'
    core_embeddings_model = HuggingFaceEmbeddings(model_name=embed_model_id)
    embedder = CacheBackedEmbeddings.from_bytes_store(core_embeddings_model, store, namespace=embed_model_id)
    vectorstore = FAISS.from_documents(texts, embedder).as_retriever(search_kwargs={"k": 10})

    # Initialize the LLM
    model_checkpoint = "MBZUAI/LaMini-Flan-T5-248M"
    tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_checkpoint)
    # Create a pipeline for text generation using the loaded model and tokenizer
    pipe = pipeline(
        'text2text-generation',
        model=model,
        tokenizer=tokenizer,
        max_length=512,
        top_k=50,  # Enabling top-k sampling
        top_p=0.9,  # Enabling nucleus sampling
        repetition_penalty=1.2
    )
    llm = HuggingFacePipeline(pipeline=pipe)

    # Apply Re-ranking
    compressor = FlashrankRerank()
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=vectorstore
    )

    # Set up the QA chain
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=compression_retriever,
        return_source_documents=False
    )

    return qa