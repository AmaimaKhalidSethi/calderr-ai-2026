#!/usr/bin/env python3
"""
Lab 1.1: Your First Groq Agent
CalderR Internship Program — Week 1

A terminal-based conversational agent using Groq + LangChain.
Maintains full conversation history across turns.

Commands:
  /clear   — wipe conversation history and start fresh
  /exit    — quit the chatbot
  /history — show all messages so far
  /help    — show available commands

Security:
  - API key via .env only, never hardcoded
  - User input length bounded to prevent runaway context
  - No shell execution, no file access

Usage:
  python lab_1_1_chatbot.py
  python lab_1_1_chatbot.py --persona "You are a Python expert..."
  python lab_1_1_chatbot.py --model openai/gpt-oss-20b

Written for: langchain-groq==1.1.3, langchain-core==1.4.8
"""

import argparse
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich import box

# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_MODEL   = "openai/gpt-oss-20b"
DEFAULT_PERSONA = (
    "You are a helpful, knowledgeable AI assistant. "
    "Be concise and direct. If you don't know something, say so clearly."
)
MAX_INPUT_LEN   = 2000   # chars — prevents runaway context growth
MAX_HISTORY     = 40     # messages before oldest non-system messages are trimmed

COMMANDS = {
    "/clear":   "Wipe conversation history and start fresh",
    "/history": "Show all messages in the current conversation",
    "/exit":    "Quit the chatbot",
    "/help":    "Show this help message",
}

console = Console()


# ── Token Usage Display ───────────────────────────────────────────────────────

def _extract_token_usage(response: AIMessage) -> dict | None:
    """Pull token usage from Groq's response metadata.

    Groq returns usage under response.response_metadata['token_usage']:
      {
        "completion_tokens": int,
        "prompt_tokens": int,
        "total_tokens": int,
        "completion_time": float,
        "prompt_time": float,
        "total_time": float,
      }
    Returns None if the key is absent (e.g. streaming or older SDK).
    """
    meta = getattr(response, "response_metadata", {})
    return meta.get("token_usage")


def print_token_usage(usage: dict | None, model: str) -> None:
    """Render a compact token usage panel below the response."""
    if usage is None:
        return

    prompt_tok  = usage.get("prompt_tokens", "?")
    compl_tok   = usage.get("completion_tokens", "?")
    total_tok   = usage.get("total_tokens", "?")
    total_time  = usage.get("total_time")
    speed       = (
        f"{compl_tok / total_time:.0f} tok/s"
        if isinstance(compl_tok, int) and isinstance(total_time, float) and total_time > 0
        else "—"
    )

    table = Table(box=box.MINIMAL, show_header=False, padding=(0, 1))
    table.add_column(style="dim")
    table.add_column(style="cyan")
    table.add_row("model",   model)
    table.add_row("prompt",  f"{prompt_tok} tokens")
    table.add_row("output",  f"{compl_tok} tokens")
    table.add_row("total",   f"{total_tok} tokens")
    table.add_row("speed",   speed)
    console.print(table)


# ── History Management ────────────────────────────────────────────────────────

def trim_history(history: list[BaseMessage], max_messages: int) -> list[BaseMessage]:
    """Keep the SystemMessage at index 0 and trim the oldest human/AI pairs
    when the history grows beyond max_messages.

    This demonstrates context window management — the model can only hold so
    much conversation before we need to drop older turns.
    """
    if len(history) <= max_messages:
        return history

    system = [m for m in history if isinstance(m, SystemMessage)]
    non_system = [m for m in history if not isinstance(m, SystemMessage)]

    # Drop the oldest non-system messages in pairs (human + AI)
    overflow = len(non_system) - (max_messages - len(system))
    trimmed = non_system[max(0, overflow):]

    if overflow > 0:
        console.print(
            f"[dim yellow]⚠ History trimmed: dropped {overflow} oldest message(s) "
            f"to stay within {max_messages}-message limit.[/dim yellow]"
        )

    return system + trimmed


def show_history(history: list[BaseMessage]) -> None:
    """Print all messages in the current conversation."""
    console.print(Rule("[bold]Conversation History[/bold]"))
    if len(history) <= 1:  # Only system message
        console.print("[dim]No conversation yet.[/dim]")
        return

    for i, msg in enumerate(history):
        if isinstance(msg, SystemMessage):
            console.print(f"[dim]SYSTEM: {msg.content[:100]}…[/dim]")
        elif isinstance(msg, HumanMessage):
            console.print(Panel(msg.content, title=f"[cyan]You[/cyan] ({i})", border_style="cyan"))
        elif isinstance(msg, AIMessage):
            console.print(Panel(Markdown(msg.content), title=f"[green]Assistant[/green] ({i})", border_style="green"))
    console.print(Rule())


# ── Command Handlers ──────────────────────────────────────────────────────────

def handle_command(cmd: str, history: list[BaseMessage], persona: str) -> list[BaseMessage]:
    """Process a /command. Returns the (possibly modified) history."""
    cmd = cmd.strip().lower()

    if cmd == "/clear":
        console.print("[yellow]Conversation cleared.[/yellow]")
        return [SystemMessage(content=persona)]   # reset to just the system message

    if cmd == "/history":
        show_history(history)
        return history

    if cmd == "/help":
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
        table.add_column("Command", style="cyan")
        table.add_column("Description")
        for c, desc in COMMANDS.items():
            table.add_row(c, desc)
        console.print(table)
        return history

    console.print(f"[red]Unknown command: {cmd}[/red]  Type /help for available commands.")
    return history


# ── LLM Call ─────────────────────────────────────────────────────────────────

def chat(llm: ChatGroq, history: list[BaseMessage]) -> AIMessage:
    """Send the full conversation history to Groq and return the response.

    Passing the entire history list is how multi-turn memory works —
    the model sees all prior turns in its context window.
    """
    response: AIMessage = llm.invoke(history)
    return response


# ── Main Loop ─────────────────────────────────────────────────────────────────

def run(model: str, persona: str, api_key: str) -> None:
    """Main REPL loop."""
    llm = ChatGroq(
        model=model,
        temperature=0.7,
        max_tokens=1024,
        timeout=30,
        groq_api_key=os.environ.get("GROQ_API_KEY"),
        max_retries=2,
    )

    # Conversation history — starts with just the system message.
    # Every user message and AI reply is appended here and passed to the LLM.
    history: list[BaseMessage] = [SystemMessage(content=persona)]

    console.print(
        Panel(
            f"[bold green]Groq Chatbot[/bold green]\n"
            f"[dim]Model: {model}[/dim]\n"
            f"[dim]Persona: {persona[:80]}{'…' if len(persona) > 80 else ''}[/dim]\n\n"
            f"[dim]Type /help for commands. Type /exit to quit.[/dim]",
            border_style="green",
        )
    )

    while True:
        # ── Get input ────────────────────────────────────────────────────────
        try:
            user_input = Prompt.ask("[cyan]You[/cyan]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye.[/dim]")
            sys.exit(0)

        if not user_input:
            continue

        # ── Handle /commands ─────────────────────────────────────────────────
        if user_input.startswith("/"):
            if user_input.lower() in ("/exit", "/quit"):
                console.print("[dim]Goodbye.[/dim]")
                sys.exit(0)
            history = handle_command(user_input, history, persona)
            continue

        # ── Validate input length ─────────────────────────────────────────────
        if len(user_input) > MAX_INPUT_LEN:
            console.print(
                f"[red]Input too long ({len(user_input)} chars). "
                f"Max: {MAX_INPUT_LEN} chars.[/red]"
            )
            continue

        # ── Append user message + call LLM ───────────────────────────────────
        history.append(HumanMessage(content=user_input))
        history = trim_history(history, MAX_HISTORY)

        try:
            with console.status("[dim]Thinking…[/dim]", spinner="dots"):
                response = chat(llm, history)
        except Exception as exc:
            console.print(f"[red]API error:[/red] {type(exc).__name__}. Try again.")
            # Remove the last human message so the user can retry
            history = history[:-1]
            continue

        # ── Append AI reply to history ────────────────────────────────────────
        history.append(response)

        # ── Render response ───────────────────────────────────────────────────
        console.print()
        console.print(
            Panel(
                Markdown(response.content),
                title="[green]Assistant[/green]",
                border_style="green",
                padding=(0, 1),
            )
        )

        # ── Show token usage ──────────────────────────────────────────────────
        usage = _extract_token_usage(response)
        print_token_usage(usage, model)
        console.print()


# ── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Lab 1.1: Groq CLI Chatbot with conversation history",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("CHAT_MODEL", DEFAULT_MODEL),
        help=f"Groq model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--persona",
        default=DEFAULT_PERSONA,
        help="System prompt / persona for the assistant",
    )
    args = parser.parse_args()

    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key or not api_key.startswith("gsk_"):
        console.print(
            "[red]GROQ_API_KEY not set or malformed.[/red]\n"
            "Copy .env.example to .env and add your key from console.groq.com"
        )
        sys.exit(1)

    run(args.model, args.persona, api_key)


if __name__ == "__main__":
    main()
