# src/rag/query_test.py

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

INDEX_PATH = "data/processed/chroma_index"

def test_query(query: str):
    """
    Loads the Chroma index and runs a similarity search against it.
    """
    print("Loading Chroma index...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    db = Chroma(
        persist_directory=INDEX_PATH,
        embedding_function=embeddings
    )

    print(f"Searching for: '{query}'")
    results = db.similarity_search(query, k=5)

    print("\nTop Results:")
    for i, r in enumerate(results, start=1):
        print(f"\nResult {i}:")
        print(f"Text: {r.page_content}")
        if r.metadata:
            print(f"Metadata keys: {list(r.metadata.keys())[:5]}")

if __name__ == "__main__":
    test_query("three point shot by Curry")
