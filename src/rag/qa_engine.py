import json
import time
from pathlib import Path
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
from langchain_huggingface import HuggingFacePipeline
from langchain_core.prompts import ChatPromptTemplate


# Automatically load the most recent summary file
SUMMARY_DIR = Path("data/structured")
SUMMARY_PATH = max(SUMMARY_DIR.glob("*_summary.json"), key=lambda p: p.stat().st_mtime)


# -------------------------------------------------------------
# Load and format summarized game data
# -------------------------------------------------------------
def load_summary(path=SUMMARY_PATH):
    with open(path, "r") as f:
        data = json.load(f)

    teams = data.get("teams", [])
    summary_text = []

    summary_text.append(f"This game featured {teams[0]} vs {teams[1]}.")
    fs = data.get("final_score", {})
    summary_text.append(
        f"Final Score — {teams[0]}: {fs.get(teams[0], 'N/A')}, {teams[1]}: {fs.get(teams[1], 'N/A')}."
    )

    def fmt_stat(stat):
        s = data.get(stat, {})
        return f"{stat.replace('_', ' ').title()} — {teams[0]}: {s.get(teams[0], 'N/A')}, {teams[1]}: {s.get(teams[1], 'N/A')}."

    for stat in ["three_pointers", "field_goals", "free_throws", "turnovers", "rebounds", "fouls", "steals"]:
        summary_text.append(fmt_stat(stat))

    narrative = data.get("narrative", "")
    if narrative:
        summary_text.append(f"Game summary: {narrative}")

    return "\n".join(summary_text)


# -------------------------------------------------------------
# Build and load the model
# -------------------------------------------------------------
def build_llm():
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
    return HuggingFacePipeline(pipeline=gen_pipeline)


# -------------------------------------------------------------
# Prompt and QA logic
# -------------------------------------------------------------
def build_prompt():
    return ChatPromptTemplate.from_template(
        "You are an NBA analyst. Use the following summarized game data to answer questions about the match.\n\n"
        "Summary:\n{context}\n\nQuestion: {question}"
    )


def ask(llm, prompt, context, question):
    print(f"\nQuestion: {question}\n")
    start = time.time()

    input_text = prompt.format(context=context, question=question)
    result = llm.invoke(input_text)

    if isinstance(result, dict) and "generated_text" in result:
        answer = result["generated_text"]
    else:
        answer = str(result)

    print("\nAnswer:", answer.strip())
    print(f"\n⏱  Completed in {time.time() - start:.1f}s\n")


# -------------------------------------------------------------
# Interactive main loop
# -------------------------------------------------------------
def main():
    context = load_summary()

    print("\n================ GAME SUMMARY CONTEXT ================\n")
    print(context)
    print("\n======================================================\n")
    
    llm = build_llm()
    prompt = build_prompt()

    print(f"\nLoaded summary file: {SUMMARY_PATH.name}")
    print("\nNBA Analyst Chat — type 'quit' to stop.\n")

    while True:
        q = input("Ask about the game: ").strip()
        if q.lower() in ["quit", "exit"]:
            print("\nExiting.")
            break
        if not q:
            continue
        ask(llm, prompt, context, q)


if __name__ == "__main__":
    main()
