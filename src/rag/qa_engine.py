import json
import time
from pathlib import Path
from openai import OpenAI
import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate


# Automatically load the most recent summary file
SUMMARY_DIR = Path("data/structured")
SUMMARY_PATH = max(SUMMARY_DIR.glob("*_summary.json"), key=lambda p: p.stat().st_mtime)


# Load environment variables from .env (if present)
load_dotenv()

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

    for stat in ["three_pointers", "field_goals", "free_throws", "turnovers", "rebounds", "fouls", "steals", "blocks", "timeouts", "substitutions"]:
        summary_text.append(fmt_stat(stat))

    narrative = data.get("narrative", "")
    if narrative:
        summary_text.append(f"Game summary: {narrative}")

    return "\n".join(summary_text)


# -------------------------------------------------------------
# Build and load the model
# -------------------------------------------------------------
def build_llm():
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    print(f"Using OpenAI model: {model}")
    client = OpenAI()

    class OpenAIChatLLM:
        def __init__(self, client, model):
            self.client = client
            self.model = model
        def invoke(self, input_text: str):
            # Simple retry to avoid sporadic empty responses
            last_content = None
            for attempt in range(1, 3):
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an NBA analyst. Answer in one short sentence (<=25 words). "
                                "Use only the provided game context. If the context lacks the information, reply exactly: 'Not enough information.' "
                                "Return only the answer with no preamble."
                            ),
                        },
                        {"role": "user", "content": input_text},
                    ],
                    max_completion_tokens=80,
                )
                content = resp.choices[0].message.content or ""
                if content.strip():
                    return content
                last_content = content
                print("⚠️ Received empty content from model, retrying... (attempt", attempt, ")")
            # Fallback: return whatever we have (possibly empty) to keep flow moving
            return last_content or ""

    return OpenAIChatLLM(client, model)


# -------------------------------------------------------------
# Prompt and QA logic
# -------------------------------------------------------------
def build_prompt():
    return ChatPromptTemplate.from_template(
        "You are an NBA analyst. Answer in one short sentence (<=50 words).\n"
        "Use only the provided game data. If the data lacks the answer, reply exactly: 'Not enough information.'\n\n"
        "Game Data:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer concisely, focusing on analysis (e.g., causes, comparisons, outcomes)."
    )


def ask(llm, prompt, context, question):
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
