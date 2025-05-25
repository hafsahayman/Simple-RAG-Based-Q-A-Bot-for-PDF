import streamlit as st
import os
from dotenv import load_dotenv
from langchain.embeddings import CohereEmbeddings
from langchain_community.llms import Cohere
from langchain.chains import create_retrieval_chain
from pinecone import Pinecone, ServerlessSpec
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from pinecone import Pinecone as PineconeClient
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore

#Loading API Key's from Environment
load_dotenv()
os.getenv('COHERE_API_KEY')
os.getenv('PINECONE_API_KEY')

#Checking if PDF and Vector store are available
if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
    
#Uploading PDF file
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

#Extracting PDF content and invoking Cohere Embedding,Pinecone
pc=PineconeClient(
    api_key=os.environ.get("PINECONE_API_KEY")
)
index_name = "quickstart"
if index_name in pc.list_indexes():
    print("yes")
    pc.create_index(
    name=index_name,
    dimension=384, 
    metric="cosine",
    spec=ServerlessSpec(cloud="aws",region="us-east-1") 
)
else:
    if uploaded_file is not None and not st.session_state.pdf_processed:
        if "embeddings" not in st.session_state:
            st.session_state.embeddings = CohereEmbeddings(model="embed-english-light-v3.0", user_agent="myapp/2.0")

        pdf_reader = PdfReader(uploaded_file)
        pdf_text = ""
        for page in pdf_reader.pages:
            pdf_text += page.extract_text()
        
        # Split the document text into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        document_chunks = text_splitter.create_documents([pdf_text])

        # Create vector store from document chunks and embeddings
        st.session_state.vector_store = PineconeVectorStore.from_documents(
            documents=document_chunks, 
            embedding=st.session_state.embeddings, 
            index_name=index_name
        )
        st.session_state.pdf_processed = True
        st.success("PDF processed and vector store created!")
        
        
    #Invoking Cohere model and creating a prompt template
    if st.session_state.pdf_processed:
        llm = Cohere(model="command-r-plus-08-2024", temperature=0.9)
        st.write("You can now query the document.")
        prompt_template = ChatPromptTemplate.from_template(
        """Answer the following questions based on the provided context.
        <context>{context}</context>
        Question: {input}"""
    )
        prompt = st.text_input("Enter your query:")
        doc_chain=create_stuff_documents_chain(llm,prompt_template)

        if prompt and st.session_state.vector_store is not None:
            retriever = st.session_state.vector_store.as_retriever()
            rc=create_retrieval_chain(retriever,doc_chain)
            response = rc.invoke({"input": prompt})
            st.write(response['answer'])
    else:
        st.info("Please upload a PDF to proceed.")

