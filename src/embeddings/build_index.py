# src/embeddings/build_index.py

import pandas as pd
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from pathlib import Path

DATA_PATH = Path("data/raw")
INDEX_PATH = Path("data/processed/chroma_index")
INDEX_PATH.mkdir(parents=True, exist_ok=True)


def build_index(csv_filename: str = "0022500142_game_data.csv"):
    """
    Builds a Chroma vector index from NBA play-by-play data
    using a local Hugging Face embedding model.
    """
    csv_path = DATA_PATH / csv_filename
    if not csv_path.exists():
        raise FileNotFoundError(f"File not found: {csv_path}")

    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)

    df["text"] = (
        df[["PCTIMESTRING", "HOMEDESCRIPTION", "VISITORDESCRIPTION"]]
        .fillna("")
        .agg(" ".join, axis=1)
    )

    print("Initializing Hugging Face embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    print("Creating Chroma vector index...")
    db = Chroma.from_texts(
        texts=df["text"].tolist(),
        embedding=embeddings,
        metadatas=df.to_dict("records"),
        persist_directory=str(INDEX_PATH)
    )

    print(f"Chroma index successfully saved to {INDEX_PATH}")


if __name__ == "__main__":
    build_index()
