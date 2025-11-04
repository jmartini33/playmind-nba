from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
import pandas as pd
import re
import time

INDEX_PATH = "data/processed/chroma_index"


# -------------------------------------------------------------
# Summarize retrieved raw game text into structured info
# -------------------------------------------------------------
def summarize_game_data(raw_context: str) -> str:
    """Convert raw play-by-play lines into a quick summary."""
    if not isinstance(raw_context, str):
        raw_context = str(raw_context)

    lines = [str(l).strip() for l in raw_context.split("\n") if str(l).strip()]
    df = pd.DataFrame({"desc": lines})

    team_names = set()
    home_3pt, away_3pt = 0, 0

    for row in df["desc"]:
        text = str(row)
        if "3PT" in text:
            if "HOMEDESCRIPTION" in text or "HOME" in text:
                home_3pt += 1
            elif "VISITORDESCRIPTION" in text or "AWAY" in text:
                away_3pt += 1
        m = re.findall(r"[A-Z][a-z]+", text)
        if m:
            team_names.update(m)

    summary = (
        f"Detected teams: {', '.join(list(team_names)[:2]) or 'Unknown'}. "
        f"Home 3-pointers: {home_3pt}, Away 3-pointers: {away_3pt}. "
        f"Total 3PT events: {home_3pt + away_3pt}."
    )
    return summary


# -------------------------------------------------------------
# Build the RAG chain
# -------------------------------------------------------------
def build_chain():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = Chroma(persist_directory=INDEX_PATH, embedding_function=embeddings)
    retriever = db.as_retriever(search_kwargs={"k": 2})

    print("Loading Flan-T5-Base model (fast CPU mode)...")
    model_id = "google/flan-t5-base"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_id)

    gen_pipeline = pipeline(
        "text2text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=128,
        truncation=True,
    )

    llm = HuggingFacePipeline(pipeline=gen_pipeline)

    prompt = ChatPromptTemplate.from_template(
        "You are an NBA analyst. Use the following game summary to answer concisely.\n\n"
        "Summary:\n{context}\n\nQuestion: {question}"
    )

    def retrieve_context(inputs):
        """Retrieve relevant documents based on the user's question."""
        question = inputs["question"]
        docs = retriever.invoke(question)
        return {"context": docs, "question": question}

    def preprocess(inputs):
        """Flatten and clean retrieved documents before summarization."""
        ctx = inputs.get("context", "")
        text_blocks = []

        if isinstance(ctx, list):
            for item in ctx:
                if hasattr(item, "page_content"):
                    text_blocks.append(str(item.page_content))
                elif isinstance(item, dict) and "page_content" in item:
                    text_blocks.append(str(item["page_content"]))
                else:
                    text_blocks.append(str(item))
        else:
            text_blocks.append(str(ctx))

        flat_context = "\n".join(text_blocks)
        print(f"\n[Preprocessor] Retrieved {len(text_blocks)} chunks, {len(flat_context)} chars total.\n")

        summary = summarize_game_data(flat_context)
        return {"context": summary, "question": inputs["question"]}

    chain = (
        RunnableLambda(retrieve_context)
        | RunnableLambda(preprocess)
        | prompt
        | llm
    )
    return chain


# -------------------------------------------------------------
# Execute a question and print the result
# -------------------------------------------------------------
def ask(chain, question: str):
    print(f"\nQuestion: {question}\n")
    start = time.time()
    print("Fetching and summarizing context...", flush=True)
    print("Generating answer...", end="", flush=True)

    answer = chain.invoke({"question": question})
    print("\n\nRaw model output:", answer)

    if isinstance(answer, list) and len(answer) > 0 and "generated_text" in answer[0]:
        text = answer[0]["generated_text"]
    else:
        text = str(answer)

    print(f"\nAnswer:\n{text}")
    print(f"\nCompleted in {time.time() - start:.1f} seconds\n")


# -------------------------------------------------------------
# Interactive main loop
# -------------------------------------------------------------
def main():
    chain = build_chain()
    print("\nNBA Analyst Chat — type 'quit' or 'exit' to stop.\n")

    while True:
        question = input("Ask about this game: ").strip()
        if question.lower() in ["quit", "exit"]:
            print("\nExiting.\n")
            break
        if not question:
            continue
        ask(chain, question)


if __name__ == "__main__":
    main()
