"""
A custom RAG store class to abstract the functionality and decouple it from the agent design and
implementation, that allows for easy switching of embedding models, vector stores and other RAG essentials for better performance and scaling without clutering or modifying the agent.
"""


import os
import json
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

class AgentVectorStore:
    def __init__(self, store_directory: str = "data/chroma_db", api_key: str | None = None):
        """Initialize the vector store, with embedding model, chunker and the store"""
        self.store_directory = store_directory
        self.embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001", api_key=api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
        self.vector_store = Chroma(
            collection_name="autostream-kb",
            embedding_function=self.embeddings,
            persist_directory=self.store_directory,
        )

    def ingest_file(self, file_path: str) -> str:
        """Ingest a single file into the vector store, with support for .md and .json files.(based on requirements, can be easily expanded to support more file formats)"""
        if not os.path.exists(file_path):
            return f"Error: {file_path} not found."
        
        filename = os.path.basename(file_path)
        docs = []

        if filename.endswith(".md"):
            with open(file_path, "r", encoding="utf-8") as file:
                docs.append(Document(page_content=file.read(), metadata = {"source": filename}))
        elif filename.endswith(".json"):
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                docs.append(Document(page_content=json.dumps(data, indent=2), metadata = {"source": filename}))
        else:
            return f"Skipped {filename}: Unsupported format."

        if docs:
            splits = self.text_splitter.split_documents(docs)
            self.vector_store.add_documents(splits)
            return f"Ingested {filename} ({len(splits)} chunks)"
        return "Failed to ingest file."

    def ingest_directory(self, directory: str) ->str:
        """Ingest all files from the given directory into the vector store(uses ingest_file internally)"""
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            return f"Empty directory created, please add documents and try again."
        results = []
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                results.append(self.ingest_file(file_path))
        return "\n".join(results) if results else "No file found."

    def search(self, query:str, k: int = 2) -> str:
        docs = self.vector_store.similarity_search(query, k=k)
        return "\n\n".join([doc.page_content for doc in docs]) if docs else "No relevant context found."