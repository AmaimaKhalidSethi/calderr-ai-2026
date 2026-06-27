"""
The two tools this ReAct agent can call, exactly as specified in the lab brief:
    1. Search a mock "database" of facts
    2. Calculate math expressions using eval()

Both are intentionally simple — the point of this lab is the AGENT LOOP
(deciding which tool to call, executing it, feeding the result back), not
the tools themselves.
"""

import re

# A small, fixed "database" of facts. Real keys are lowercase, single
# words or short phrases — the search tool does a simple substring match,
# not anything fancy (no embeddings, no fuzzy matching — that would be a
# different lab's concept, not this one's).
MOCK_FACT_DATABASE = {
    "python": "Python was created by Guido van Rossum and first released in 1991.",
    "groq": "Groq is an AI infrastructure company known for very fast LLM inference using custom LPU hardware.",
    "streamlit": "Streamlit is an open-source Python framework for building data/ML web apps with minimal code.",
    "pydantic": "Pydantic is a Python library for data validation using type hints, widely used for structuring LLM outputs.",
    "react pattern": "ReAct (Reasoning + Acting) is a prompting pattern where a model alternates between reasoning steps and tool-calling actions, introduced in a 2022 paper by Yao et al.",
    "transformer": "The Transformer architecture, introduced in 'Attention Is All You Need' (2017), underlies almost all modern large language models.",
    "token": "A token is the basic unit of text an LLM processes — roughly 3/4 of a word in English on average.",
    "context window": "A context window is the maximum number of tokens a model can process in a single request, including both input and output.",
    "temperature": "Temperature controls randomness in LLM sampling — 0 is deterministic/greedy, higher values increase diversity and unpredictability.",
    "rawalpindi": "Rawalpindi is a city in Punjab, Pakistan, adjacent to the capital Islamabad.",
}


def search_facts(query: str) -> str:
    """Mock database search tool. Does a case-insensitive substring match
    against fact keys. Returns the matched fact, or a clear 'not found'
    message — the agent needs to be able to observe failure too, not just
    success, since that's part of what makes the loop realistic."""
    query_lower = query.strip().lower()

    # exact key match first
    if query_lower in MOCK_FACT_DATABASE:
        return MOCK_FACT_DATABASE[query_lower]

    # substring match: does the query contain a known key, or vice versa
    for key, fact in MOCK_FACT_DATABASE.items():
        if key in query_lower or query_lower in key:
            return fact

    available = ", ".join(sorted(MOCK_FACT_DATABASE.keys()))
    return f"No fact found for '{query}'. Available topics: {available}"


# Only allow digits, basic operators, parentheses, decimal points, and
# whitespace before ever calling eval(). This is a deliberate, narrow
# allowlist — eval() on arbitrary text is a real code-execution risk, and
# "use eval()" in the lab brief means use it for the ARITHMETIC, not
# without any guardrail at all. Rejecting anything outside this pattern
# means even if the model ever passed something unexpected, it can't reach
# eval() with it.
_SAFE_MATH_PATTERN = re.compile(r"^[\d\s\.\+\-\*\/\(\)\%]+$")


def calculate(expression: str) -> str:
    """Evaluates a basic math expression using eval(), restricted to a
    narrow character allowlist checked BEFORE eval() ever runs."""
    expression = expression.strip()

    if not expression:
        return "Error: empty expression."

    if not _SAFE_MATH_PATTERN.match(expression):
        return (
            f"Error: '{expression}' contains characters outside the allowed "
            f"set (digits, + - * / % ( ) and decimal points only). Refusing "
            f"to evaluate for safety."
        )

    try:
        # eval() is used here per the lab's explicit instruction, but only
        # ever on a string that has already passed the character allowlist
        # above — it can't reach arbitrary Python this way.
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except ZeroDivisionError:
        return f"Error: division by zero in '{expression}'."
    except Exception as e:
        return f"Error evaluating '{expression}': {e}"
