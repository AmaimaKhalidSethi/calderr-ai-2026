"""
Lab 1.2 — Manual ReAct Loop. CLI entry point.

Run interactively:
    python main.py

Run the built-in demo questions (shows tool selection across different
question types — pure search, pure calculation, and a question needing
both):
    python main.py --demo
"""

import sys

from lab1.lab_1_2.agent import run_agent

DEMO_QUESTIONS = [
    "What is 12 times 7?",
    "Who created Python and when?",
    "If Python was released in 1991, how many years old is it as of 2026?",
    "What is the capital relationship between Rawalpindi and Islamabad?",
]


def run_demo() -> None:
    for i, question in enumerate(DEMO_QUESTIONS, start=1):
        print("\n" + "=" * 70)
        print(f"DEMO QUESTION {i}: {question}")
        print("=" * 70)
        try:
            answer = run_agent(question, verbose=True)
            print(f"\n>>> ANSWER: {answer}")
        except RuntimeError as e:
            print(f"\n>>> AGENT FAILED: {e}")


def run_interactive() -> None:
    print("Manual ReAct Agent — type a question, or 'exit' to quit.")
    print("Tools available: search_facts (mock fact database), calculate (eval-based math)\n")
    while True:
        question = input("> ").strip()
        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue
        try:
            answer = run_agent(question, verbose=True)
            print(f"\n>>> ANSWER: {answer}\n")
        except RuntimeError as e:
            print(f"\n>>> AGENT FAILED: {e}\n")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        run_demo()
    else:
        run_interactive()
