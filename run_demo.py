"""Run Music Store demo from the CLI (no Jupyter required)."""

from __future__ import annotations

import os
import sys

from db import get_db, run_query
from graph import ask, build_graph, lookup_customer_id, resume
from memory_store import preference_memory
from tools_music import get_albums_by_artist


def smoke_without_llm() -> None:
    print("=== Offline smoke (DB + tools) ===")
    db = get_db()
    print("Tables:", db.get_usable_table_names())
    print("Phone -> customer:", lookup_customer_id("My phone is +55 (12) 3923-5555"))
    print("Rolling Stones albums:")
    print(get_albums_by_artist.invoke({"artist": "Rolling Stones"}))
    print("Recent invoice sample:")
    print(run_query(
        "SELECT InvoiceId, InvoiceDate, Total FROM Invoice "
        "WHERE CustomerId = 1 ORDER BY InvoiceDate DESC LIMIT 3;"
    ))


def run_testcases(api_key: str) -> None:
    preference_memory.clear()
    graph = build_graph(api_key)

    print("\n=== Test case 1 ===")
    q1 = (
        "My phone number is +55 (12) 3923-5555. "
        "How much was my most recent purchase? "
        "What albums do you have by the Rolling Stones?"
    )
    r1 = ask(graph, q1, thread_id="cli-testcase-1")
    print(r1)

    print("\n=== Test case 1 follow-up ===")
    r1b = ask(graph, "List some songs that match my preferences?", thread_id="cli-testcase-1")
    print(r1b)

    print("\n=== Test case 2 (expect interrupt) ===")
    q2 = (
        "How much was my most recent purchase? "
        "What albums do you have by the Rolling Stones?"
    )
    r2 = ask(graph, q2, thread_id="cli-testcase-2")
    print(r2)

    if r2.get("status") == "interrupted":
        print("\n=== Resume test case 2 ===")
        r2b = resume(graph, "+55 (12) 3923-5555", thread_id="cli-testcase-2")
        print(r2b)


def main() -> int:
    smoke_without_llm()

    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        print(
            "\nGROQ_API_KEY is not set. Offline checks passed.\n"
            "To run the full multi-agent demo:\n"
            '  $env:GROQ_API_KEY = "your_key"\n'
            "  .venv\\Scripts\\python run_demo.py\n"
        )
        return 0

    run_testcases(api_key)
    return 0


if __name__ == "__main__":
    sys.exit(main())
