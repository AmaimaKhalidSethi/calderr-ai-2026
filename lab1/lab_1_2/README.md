# Lab 1.2 — Manual ReAct Loop

A hand-written ReAct agent — no LangChain, no agent framework of any kind.
The Thought → Action → Observation loop is plain Python, in `agent.py`.

## What it does

Given a question, the agent decides, step by step, whether it needs to:
- **search a mock fact database** (`tools.py::search_facts`), or
- **calculate a math expression using `eval()`** (`tools.py::calculate`), or
- **answer directly** (`final_answer`, which ends the loop)

It can chain multiple steps — e.g. "how many years old is Python" requires
looking up Python's release year first, *then* doing the subtraction, which
takes two iterations of the loop, not one.

## Run it

```bash
pip install -r requirements.txt
```

Create a `.env` file with `GROQ_API_KEY=gsk_...` (see the parent project's
`.env.example` for the format), or export it as an environment variable.

```bash
python main.py --demo     # runs 4 built-in test questions, shows the full trace
python main.py             # interactive mode, type your own questions
```

## How the loop works

```
Thought:      model reasons about what it needs to do next
Action:       model picks search_facts / calculate / final_answer
Observation:  the TOOL's result (not the model) is fed back into the
              next call's prompt
... repeats until final_answer or 6 iterations ...
```

This is the same loop the Week 1 material describes two ways — they're the
same thing under different names:

| ReAct paper | Agent Loop framing | This code |
|---|---|---|
| Thought | Plan | `AgentStep.thought` |
| Action | Act | `run_tool()` — executed in Python, not by the model |
| Observation | Observe | tool's return value, appended to the transcript |
| (transcript re-read each call) | Perceive | `AgentTranscript.render_for_prompt()` |

## One deliberate deviation from "textbook" ReAct

The original ReAct paper has the model output plain text like
`Action: calculator[2+2]` and parses it with string matching/regex. This
implementation uses Groq's `strict: true` JSON schema mode instead
(`models.py::AgentStep`) — the model picks `action` from a fixed enum and
provides `action_input` as a structured field, rather than free text.

This is **not** "using a framework" — Pydantic is a data-validation
library, not an agent framework, and is explicitly a named Week 1 skill.
The loop itself (deciding when to stop, executing tools, feeding results
back) is still fully hand-written here. Structured output just makes tool
selection reliable rather than dependent on regex parsing free text
correctly every time — the same lesson learned the hard way in the
Project 1-P-C build (see that project's README for the live failures that
motivated using strict mode there).

## Safety note on `eval()`

`calculate()` runs input through a strict character allowlist (digits,
`+ - * / % ( ) .` and whitespace only) **before** it ever reaches `eval()`.
This was verified against actual injection attempts
(`__import__('os').system(...)`, `[].__class__.__base__...`, chained
statements via `;`) — all rejected before reaching `eval()`. The lab brief
asks to use `eval()` for arithmetic; it doesn't ask for an unguarded
`eval()` on arbitrary text, which would be a real code-execution risk.

## Files

| File | Purpose |
|---|---|
| `tools.py` | The two tools: mock fact search, guarded `eval()` calculator |
| `models.py` | `AgentStep` — the Pydantic schema for one loop iteration |
| `agent.py` | The loop itself: `run_agent()`, `get_next_step()`, `run_tool()`, `AgentTranscript` |
| `main.py` | CLI — `--demo` mode or interactive mode |
