import os
import shutil
import subprocess
import stat
import tempfile
import streamlit as st
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

REPO_PATH = "./cloned_repo"
DB_PATH = "./dynamic_qdrant_db"

def remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)

@st.cache_resource(show_spinner=False)
def get_vectorstore():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    client = QdrantClient(path=DB_PATH)
    return QdrantVectorStore(client=client, collection_name="dynamic_repo", embedding=embeddings)

def procesar_repositorio(github_url):
    st.cache_resource.clear()
    if os.path.exists(REPO_PATH):
        shutil.rmtree(REPO_PATH, onerror=remove_readonly)
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH, onerror=remove_readonly)
    
    subprocess.run(["git", "clone", github_url, REPO_PATH], check=True)
    
    loader = GenericLoader.from_filesystem(
        REPO_PATH, glob="**/*", suffixes=[".py"],
        parser=LanguageParser(language=Language.PYTHON, parser_threshold=50)
    )
    docs = loader.load()
    
    python_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON, chunk_size=2000, chunk_overlap=200
    )
    texts = python_splitter.split_documents(docs)
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    QdrantVectorStore.from_documents(
        texts, embeddings, path=DB_PATH, collection_name="dynamic_repo", force_recreate=True
    )
    return len(texts)

def procesar_reglas_empresa(uploaded_file):
    texto_completo = ""
    if uploaded_file.name.endswith(".pdf"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        loader = PyPDFLoader(tmp_path)
        docs = loader.load()
        texto_completo = "\n\n".join([doc.page_content for doc in docs])
        os.remove(tmp_path)
    else:
        raw_bytes = uploaded_file.getvalue()
        try:
            texto_completo = raw_bytes.decode("utf-8")
        except:
            texto_completo = raw_bytes.decode("latin-1", errors="ignore")
    
    reglas_actuales = st.session_state.get("reglas_corporativas", "")
    st.session_state.reglas_corporativas = reglas_actuales + f"\n\n--- DOCUMENTO ASIMILADO: {uploaded_file.name} ---\n\n" + texto_completo
    return True