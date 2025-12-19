import os
from pathlib import Path
from dotenv import load_dotenv

import gradio as gr

# Vector store + embeddings + document loaders
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# FREE Gemini API
from langchain_google_genai import ChatGoogleGenerativeAI

# LangChain Core (LCEL)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


# ---------------------------
# Load environment variables
# ---------------------------

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY in .env")

DATA_DIR = Path("data/company_policies")
CHROMA_DIR = "chroma_db"


# ---------------------------
# Build Vector DB
# ---------------------------

def build_vectorstore():
    loader = DirectoryLoader(
        str(DATA_DIR),
        glob="*.pdf",
        loader_cls=PyPDFLoader
    )
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectordb = Chroma.from_documents(
        chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )
    return vectordb


def load_vectorstore():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    return Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings
    )


def get_vectorstore():
    if os.path.exists(CHROMA_DIR) and os.listdir(CHROMA_DIR):
        return load_vectorstore()
    return build_vectorstore()


# ---------------------------
# Build RAG Pipeline (Free Gemini API)
# ---------------------------

def create_rag_pipeline(vectordb):

    retriever = vectordb.as_retriever(search_kwargs={"k": 4})

    # FREE GEMINI LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0
    )

    prompt = ChatPromptTemplate.from_template(
        """
        You are an HR assistant. Use ONLY the provided documents to answer.
        If unsure, reply with: "I’m not sure based on the company documents."

        Context:
        {context}

        Question:
        {question}
        """
    )

    def combine_docs(docs):
        return "\n\n".join([d.page_content for d in docs])

    rag_chain = (
        {
            "context": retriever | combine_docs,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


# ---------------------------
# Gradio UI
# ---------------------------

def create_chatbot():

    vectordb = get_vectorstore()
    rag = create_rag_pipeline(vectordb)

    def chat_fn(message, history):
        response = rag.invoke(message)
        return response

    return gr.ChatInterface(
        fn=chat_fn,
        title="HR Policy Assistant (Gemini 1.5 Flash – FREE API)",
        description="Ask questions about leaves, hiring, policies, WFH, benefits…"
    )


if __name__ == "__main__":
    ui = create_chatbot()
    ui.launch()
