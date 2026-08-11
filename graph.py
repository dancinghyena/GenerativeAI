"""LangGraph multi-agent customer support workflow for the music store."""

from __future__ import annotations

import re
from typing import Annotated, Literal, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.types import Command, interrupt
from typing_extensions import TypedDict

from db import run_query
from memory_store import preference_memory
from tools_invoice import INVOICE_TOOLS, get_invoices_by_customer_sorted_by_date
from tools_music import (
    MUSIC_TOOLS,
    get_albums_by_artist,
    get_songs_by_genre,
    get_tracks_by_artist,
)


def _keep_existing(existing: str, new: str) -> str:
    """Do not overwrite a known customer_id / memory with empty values."""
    return new if new else (existing or "")


class State(TypedDict):
    """Represents the state of our LangGraph agent."""

    customer_id: Annotated[str, _keep_existing]
    messages: Annotated[list[AnyMessage], add_messages]
    loaded_memory: Annotated[str, _keep_existing]
    route: str


def get_llm(api_key: str, model: str = "llama-3.3-70b-versatile"):
    return ChatGroq(api_key=api_key, model=model, temperature=0)


def _last_user_text(messages) -> str:
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", None) == "human":
            return msg.content if isinstance(msg.content, str) else str(msg.content)
    return ""


def _normalize_phone(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _first_id_from_query(result: str) -> str:
    if not result or result.strip() in {"", "[]"}:
        return ""
    match = re.search(r"\b(\d+)\b", result)
    return match.group(1) if match else ""


def lookup_customer_id(text: str) -> str:
    """Map customer ID / email / phone mentioned in text to a CustomerId."""
    if not text:
        return ""

    id_match = re.search(r"\b(?:customer\s*(?:id)?|id)\s*[:=]?\s*(\d+)\b", text, re.I)
    if id_match:
        cid = id_match.group(1)
        result = run_query(f"SELECT CustomerId FROM Customer WHERE CustomerId = {int(cid)};")
        if _first_id_from_query(result):
            return cid

    # Bare numeric id when the whole message is just an id
    if text.strip().isdigit():
        cid = text.strip()
        result = run_query(f"SELECT CustomerId FROM Customer WHERE CustomerId = {int(cid)};")
        if _first_id_from_query(result):
            return cid

    email_match = re.search(r"[\w.+-]+@[\w.-]+\.\w+", text)
    if email_match:
        email = email_match.group(0).replace("'", "''")
        result = run_query(
            f"SELECT CustomerId FROM Customer WHERE lower(Email) = lower('{email}');"
        )
        found = _first_id_from_query(result)
        if found:
            return found

    phone_candidates = re.findall(r"\+?\d[\d\s().-]{7,}\d", text)
    if phone_candidates:
        customers = run_query("SELECT CustomerId, Phone FROM Customer;")
        rows = re.findall(r"\((\d+),\s*'([^']*)'\)", customers or "")
        if not rows:
            # Alternate formatting from SQLDatabase
            lines = [ln for ln in (customers or "").splitlines() if ln.strip()]
            for candidate in phone_candidates:
                digits = _normalize_phone(candidate)
                for ln in lines:
                    if digits and _normalize_phone(ln)[-8:] == digits[-8:]:
                        maybe = re.search(r"\b(\d+)\b", ln)
                        if maybe:
                            return maybe.group(1)
        for candidate in phone_candidates:
            digits = _normalize_phone(candidate)
            if len(digits) < 8:
                continue
            for cid, phone in rows:
                phone_digits = _normalize_phone(phone)
                if digits == phone_digits or digits[-8:] == phone_digits[-8:]:
                    return str(cid)

    return ""


def needs_customer_identity(text: str) -> bool:
    """Invoice/account questions require a verified customer."""
    lowered = (text or "").lower()
    keywords = [
        "my purchase",
        "my invoice",
        "my invoices",
        "most recent purchase",
        "my order",
        "how much did i",
        "how much was my",
        "my bill",
        "support rep",
        "my employee",
        "my preferences",
        "match my preference",
    ]
    return any(k in lowered for k in keywords)


def verify_customer(state: State) -> dict:
    """Verify customer identity; interrupt if required info is missing."""
    text = _last_user_text(state["messages"])
    customer_id = state.get("customer_id") or ""

    found = lookup_customer_id(text)
    if found:
        customer_id = found

    if needs_customer_identity(text) and not customer_id:
        answer = interrupt(
            {
                "prompt": (
                    "I need to verify your identity before answering account questions. "
                    "Please provide your Customer ID, email, or phone number."
                )
            }
        )
        if isinstance(answer, dict):
            answer = answer.get("data") or answer.get("value") or str(answer)
        customer_id = lookup_customer_id(str(answer))
        if not customer_id:
            return {
                "customer_id": "",
                "messages": [
                    AIMessage(
                        content=(
                            "I still could not verify your identity. "
                            "Please provide a valid Customer ID, email, or phone number."
                        )
                    )
                ],
                "route": "blocked",
            }

    return {"customer_id": customer_id or state.get("customer_id", "")}


def load_memory(state: State) -> dict:
    cid = state.get("customer_id") or ""
    return {"loaded_memory": preference_memory.load(cid)}


def supervisor(state: State) -> dict:
    """Route to music, invoice, or both based on the latest user question."""
    text = _last_user_text(state["messages"]).lower()
    music_keys = [
        "album",
        "albums",
        "song",
        "songs",
        "track",
        "artist",
        "genre",
        "music",
        "recommend",
        "rolling stones",
        "preference",
        "catalog",
    ]
    invoice_keys = [
        "invoice",
        "purchase",
        "bought",
        "order",
        "bill",
        "payment",
        "employee",
        "support rep",
        "how much",
    ]

    wants_music = any(k in text for k in music_keys)
    wants_invoice = any(k in text for k in invoice_keys)

    if wants_music and wants_invoice:
        route = "both"
    elif wants_invoice:
        route = "invoice"
    else:
        route = "music"

    return {"route": route}


def _inject_customer_id(tool_name: str, args: dict, customer_id: str) -> dict:
    invoice_tools = {
        "get_invoices_by_customer_sorted_by_date",
        "get_invoices_sorted_by_unit_price",
        "get_employee_by_invoice_and_customer",
    }
    if tool_name in invoice_tools and not args.get("customer_id"):
        args = {**args, "customer_id": customer_id}
    return args


def _music_fallback(question: str, memory: str) -> str:
    """Deterministic catalog lookup if Groq tool-calling fails."""
    q = (question or "").lower()
    mem = (memory or "").lower()
    parts = []

    artist_match = re.search(
        r"(?:by|from)\s+(?:the\s+)?([a-z0-9][\w\s&/'-]{1,40})", q, re.I
    )
    artist = artist_match.group(1).strip() if artist_match else ""
    if not artist:
        for name in ["rolling stones", "metallica", "queen", "ac/dc", "beatles", "u2"]:
            if name in q or name in mem:
                artist = name
                break

    if artist and ("album" in q or "albums" in q):
        parts.append(f"Albums for {artist.title()}:\n{get_albums_by_artist.invoke({'artist': artist})}")
    if artist and any(k in q for k in ["song", "songs", "track", "preference"]):
        parts.append(f"Tracks for {artist.title()}:\n{get_tracks_by_artist.invoke({'artist': artist})}")
    if "genre" in q:
        genre_match = re.search(r"\b(rock|jazz|metal|classical|blues|latin|reggae)\b", q, re.I)
        if genre_match:
            g = genre_match.group(1)
            parts.append(f"Songs in {g}:\n{get_songs_by_genre.invoke({'genre': g})}")
    if not parts and artist:
        parts.append(f"Albums for {artist.title()}:\n{get_albums_by_artist.invoke({'artist': artist})}")
        parts.append(f"Tracks for {artist.title()}:\n{get_tracks_by_artist.invoke({'artist': artist})}")
    if not parts and mem:
        parts.append(f"Tracks for preferences ({memory}):\n{get_tracks_by_artist.invoke({'artist': memory})}")
    return "\n\n".join(parts) if parts else "No matching catalog results found."


def _invoice_fallback(customer_id: str, question: str) -> str:
    if not customer_id:
        return "Customer ID is required for invoice lookup."
    data = get_invoices_by_customer_sorted_by_date.invoke({"customer_id": customer_id})
    return f"Invoices for customer {customer_id} (most recent first):\n{data}"


def _summarize_with_llm(llm, system: str, question: str, tool_data: str) -> AIMessage:
    """Ask the LLM to phrase an answer from already-fetched tool data (no tool calling)."""
    try:
        response = llm.invoke(
            [
                SystemMessage(
                    content=system
                    + " Use ONLY the provided data. Do not invent facts. Be concise."
                ),
                HumanMessage(
                    content=(
                        f"User question:\n{question}\n\n"
                        f"Data from tools:\n{tool_data}\n\n"
                        "Write a helpful answer."
                    )
                ),
            ]
        )
        if isinstance(response.content, str) and response.content.strip():
            return response
    except Exception:
        pass
    return AIMessage(content=tool_data)


def music_catalog_agent(state: State, llm, focused_question: str | None = None) -> dict:
    memory = state.get("loaded_memory") or "None"
    question = focused_question or _last_user_text(state["messages"])
    tool_data = _music_fallback(question, memory)
    system = (
        "You are the Music Catalog sub-agent for a digital music store. "
        "Answer ONLY music catalog questions."
    )
    answer = _summarize_with_llm(llm, system, question, tool_data)
    return {"messages": [answer]}


def invoice_info_agent(state: State, llm, focused_question: str | None = None) -> dict:
    cid = state.get("customer_id") or ""
    question = focused_question or _last_user_text(state["messages"])
    tool_data = _invoice_fallback(cid, question)
    system = (
        "You are the Invoice Information sub-agent for a digital music store. "
        "Answer ONLY invoice/purchase questions. "
        "Clearly state the most recent purchase date and total when asked."
    )
    answer = _summarize_with_llm(llm, system, question, tool_data)
    return {"messages": [answer]}


def both_agents(state: State, llm) -> dict:
    text = _last_user_text(state["messages"])
    inv = invoice_info_agent(
        state,
        llm,
        focused_question=(
            "Answer only the purchase/invoice part of this request. "
            f"User said: {text}"
        ),
    )
    mus = music_catalog_agent(
        state,
        llm,
        focused_question=(
            "Answer only the music catalog part of this request. "
            f"User said: {text}"
        ),
    )
    combined = (
        "I've found the information you requested:\n\n"
        f"{inv['messages'][0].content}\n\n"
        f"{mus['messages'][0].content}"
    )
    return {"messages": [AIMessage(content=combined)]}


def save_memory(state: State, llm) -> dict:
    """Extract and persist simple music preferences from the conversation."""
    cid = state.get("customer_id") or ""
    if not cid:
        return {}

    text = _last_user_text(state["messages"])
    prefs = []
    for artist in ["rolling stones", "beatles", "metallica", "queen", "ac/dc", "u2"]:
        if artist in text.lower():
            prefs.append(artist.title())
    genre_match = re.search(
        r"\b(rock|jazz|metal|classical|blues|latin|reggae)\b", text, re.I
    )
    if genre_match:
        prefs.append(genre_match.group(1).title())

    if prefs:
        preference_memory.save(cid, ", ".join(prefs))
    elif any(k in text.lower() for k in ["album", "artist", "song", "genre"]):
        try:
            result = llm.invoke(
                [
                    SystemMessage(
                        content=(
                            "Extract music preferences (artists or genres) from the user message. "
                            "Return a short comma-separated list, or NONE."
                        )
                    ),
                    HumanMessage(content=text),
                ]
            )
            content = (result.content or "").strip()
            if content and content.upper() != "NONE":
                preference_memory.save(cid, content)
        except Exception:
            pass

    return {"loaded_memory": preference_memory.load(cid)}


def route_after_verify(state: State) -> Literal["load_memory", "__end__"]:
    if state.get("route") == "blocked":
        return END
    if needs_customer_identity(_last_user_text(state["messages"])) and not state.get(
        "customer_id"
    ):
        last = state["messages"][-1] if state["messages"] else None
        if isinstance(last, AIMessage):
            return END
    return "load_memory"


def route_from_supervisor(state: State) -> Literal["music", "invoice", "both"]:
    return state.get("route") or "music"  # type: ignore[return-value]


def build_graph(api_key: str):
    """Compile the multi-agent support graph with interrupt/resume support."""
    llm = get_llm(api_key)

    builder = StateGraph(State)
    builder.add_node("verify_customer", verify_customer)
    builder.add_node("load_memory", load_memory)
    builder.add_node("supervisor", supervisor)
    builder.add_node("music", lambda s: music_catalog_agent(s, llm))
    builder.add_node("invoice", lambda s: invoice_info_agent(s, llm))
    builder.add_node("both", lambda s: both_agents(s, llm))
    builder.add_node("save_memory", lambda s: save_memory(s, llm))

    builder.add_edge(START, "verify_customer")
    builder.add_conditional_edges(
        "verify_customer",
        route_after_verify,
        {"load_memory": "load_memory", END: END},
    )
    builder.add_edge("load_memory", "supervisor")
    builder.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {"music": "music", "invoice": "invoice", "both": "both"},
    )
    builder.add_edge("music", "save_memory")
    builder.add_edge("invoice", "save_memory")
    builder.add_edge("both", "save_memory")
    builder.add_edge("save_memory", END)

    return builder.compile(checkpointer=MemorySaver())


def _interrupt_payload(graph, config) -> Optional[dict]:
    snapshot = graph.get_state(config)
    if snapshot.tasks:
        for task in snapshot.tasks:
            if task.interrupts:
                return {
                    "status": "interrupted",
                    "prompt": task.interrupts[0].value,
                    "customer_id": (snapshot.values or {}).get("customer_id", ""),
                }
    return None


def ask(graph, question: str, thread_id: str = "default"):
    """Start or continue a turn with a user question."""
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke(
        {"messages": [HumanMessage(content=question)], "route": ""},
        config=config,
    )
    interrupted = _interrupt_payload(graph, config)
    if interrupted:
        return interrupted

    messages = result.get("messages", [])
    return {
        "status": "ok",
        "customer_id": result.get("customer_id", ""),
        "answer": messages[-1].content if messages else "",
        "loaded_memory": result.get("loaded_memory", ""),
    }


def resume(graph, human_reply: str, thread_id: str = "default"):
    """Resume after a human-in-the-loop interrupt with the provided credentials/info."""
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke(Command(resume=human_reply), config=config)
    interrupted = _interrupt_payload(graph, config)
    if interrupted:
        return interrupted

    messages = result.get("messages", [])
    return {
        "status": "ok",
        "customer_id": result.get("customer_id", ""),
        "answer": messages[-1].content if messages else "",
        "loaded_memory": result.get("loaded_memory", ""),
    }
