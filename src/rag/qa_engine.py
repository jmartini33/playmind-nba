from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
import time

from src.utils.preprocess import summarize_game_data, preprocess_context

INDEX_PATH = "data/processed/chroma_index"


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

    chain = (
        RunnableLambda(retrieve_context)
        | RunnableLambda(preprocess_context)
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
