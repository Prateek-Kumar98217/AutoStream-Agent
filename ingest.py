"""
A small script to easily populate the vectore store for the agent.
Manual changes to vectore db prefered due to the nature of data stored within it(Official company and product related statements)
"""

from demo.core.rag import AgentVectorStore
from demo.config import settings

def main():
    print("Initializing Vector Store...")
    vector_store = AgentVectorStore(
        store_directory=settings.STORE_DIR, 
        api_key=settings.GEMINI_API_KEY
    )
    kb_dir = "demo/data/knowledge_base"
    print(f"Ingesting documents from {kb_dir}...")
    result = vector_store.ingest_directory(kb_dir)

    print(result)

if __name__ == "__main__":
    main()