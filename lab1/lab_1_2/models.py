"""
Pydantic schema for one step of the manual ReAct loop.

This is the ONE place this lab uses structured output instead of classic
ReAct's plain-text "Action: tool[input]" parsing. The lab brief says "no
framework" (meaning: no LangChain agent executor, no ReAct library doing
the loop for you) — it does not say "no Pydantic," which is explicitly a
named Week 1 skill. Using strict-mode JSON here (same technique verified
in Project 1-P-C) makes tool selection reliable rather than dependent on
regex-parsing free text, while the loop itself — the Thought -> Action ->
Observation cycle, deciding when to stop, feeding results back in — is
still hand-written here, not delegated to any framework.

Mapped to the two equivalent framings from the Week 1 doc:
    ReAct paper:      Thought      -> Action         -> Observation
    Agent Loop:        Perceive     -> Plan            -> Act      -> Observe
    This schema:       (perceive is "read the conversation so far")
                        thought      action+action_input  (executed
                        outside the model, then fed back as an Observation)
"""

from pydantic import BaseModel, ConfigDict
from typing import Literal


class AgentStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thought: str
    # Three possible actions: two real tools, plus "final_answer" — the
    # model's way of signalling "I have enough information, stop looping."
    # This is what makes it a LOOP rather than a fixed pipeline (contrast
    # with Project 1-P-C, which always runs a fixed number of stages):
    # the model itself decides when to stop, each iteration.
    action: Literal["search_facts", "calculate", "final_answer"]
    # Semantics depend on `action`:
    #   - search_facts / calculate: the input to pass to that tool
    #   - final_answer: the actual answer text to show the user
    action_input: str
