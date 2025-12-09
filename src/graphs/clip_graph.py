"""LangGraph: NL prompt → SML-style clip JSON → DB clip.

This is a minimal, end-to-end example you can dissect.

Flow:
 1. State contains a `prompt` string.
 2. `generate_sml_clip` node calls OpenAI with the GENERATE_CLIP_FROM_NL_SCHEMA
    tool schema to get a structured clip description (bars/items).
 3. Node adapts that tool output into the SML clip format we already support.
 4. `store_clip` node parses SML → AST → spec/DSL → stores in DB via ClipService.

Requirements (install):
    pip install langgraph langchain-core openai

Environment variables expected:
    OPENAI_API_KEY   # for OpenAI
    DATABASE_URL     # e.g. postgresql+asyncpg://user:pass@host:port/dbname
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, Optional, TypedDict, List

from openai import OpenAI
from langgraph.graph import StateGraph, END

from src.graphs.clip_configuration import GENERATE_CLIP_FROM_NL_SCHEMA
from src.dsl.sml_ast import clip_from_smil_dict, DEFAULT_UNITS_PER_BAR
from src.services import ClipService

from dotenv import load_dotenv

load_dotenv()  # reads .env and populates os.


# -----------------------------
# LangGraph state
# -----------------------------


class ClipGenerationState(TypedDict, total=False):
    """Graph state for clip generation.

    Fields:
      - prompt: user natural language request
      - sml_clip: SML-style clip dict (bars/items) ready for storage
      - clip_id: ID of the stored clip in the database
      - error: error message if something went wrong
    """

    prompt: str
    sml_clip: Dict[str, Any]
    clip_id: int
    error: str


# -----------------------------
# Nodes
# -----------------------------


async def generate_sml_clip(state: ClipGenerationState) -> ClipGenerationState:
    """Call OpenAI to generate a structured SML-style clip from NL.

    Uses the GENERATE_CLIP_FROM_NL_SCHEMA tool schema to get a function call
    result, then adapts it into the SML clip format expected by
    `clip_from_smil_dict` and `ClipService.create_clip_from_dsl`.
    """

    prompt = state.get("prompt")
    if not prompt:
        return {"error": "Missing prompt in state"}

    # OpenAI client will read OPENAI_API_KEY from the environment.
    client = OpenAI()

    try:
        resp = client.chat.completions.create(
            model="gpt-5.1",  # adjust to your available model
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a music structure parser. "
                        "Convert the user's request into a structured clip JSON "
                        "that matches the generate_clip_from_nl schema. "
                        "Only output valid arguments."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            functions=[GENERATE_CLIP_FROM_NL_SCHEMA],
            function_call={"name": "generate_clip_from_nl"},
            temperature=0,
        )

        msg = resp.choices[0].message
        if not msg.function_call or not msg.function_call.arguments:
            return {"error": "Model did not return function call arguments"}

        # Arguments is a JSON string according to OpenAI function-calling spec
        tool_args = json.loads(msg.function_call.arguments)

        # Map tool schema → SML clip dict
        # Tool schema has: clip_name, instrument, tempo_bpm, bars[ {bar_index, items, expression?} ]
        bars: List[Dict[str, Any]] = []
        for bar in tool_args.get("bars", []):
            bars.append(
                {
                    "bar_index": bar["bar_index"],
                    "items": bar.get("items", []),
                    "expression": bar.get("expression"),
                }
            )

        sml_clip = {
            # clip_id can be None; DB will assign its own PK
            "clip_id": None,
            "name": tool_args.get("clip_name") or "generated-clip",
            "track_name": tool_args.get("instrument"),
            "bars": bars,
        }

        return {**state, "sml_clip": sml_clip}

    except Exception as e:  # noqa: BLE001 - surfacing any error in graph state
        return {"error": f"OpenAI error: {e}"}


async def store_clip(state: ClipGenerationState) -> ClipGenerationState:
    """Store the generated SML clip in the database via ClipService.

    Steps:
      - Validate/parse SML dict → Clip AST (`clip_from_smil_dict`)
      - Convert AST → spec/DSL clip dict (`to_spec_clip`)
      - Store via `ClipService.create_clip_from_dsl`
    """

    if state.get("error"):
        # Propagate existing error, don't overwrite
        return state

    sml_clip = state.get("sml_clip")
    if not sml_clip:
        return {**state, "error": "No sml_clip in state"}

    # Parse SML into AST and then to spec-compliant clip dict
    try:
        clip_ast = clip_from_smil_dict(sml_clip, units_per_bar=DEFAULT_UNITS_PER_BAR)
        spec_clip = clip_ast.to_spec_clip()
    except Exception as e:  # noqa: BLE001
        return {**state, "error": f"SML → AST conversion failed: {e}"}

    # Store via async ClipService
    service = ClipService()
    try:
        clip_id = await service.create_clip_from_dsl(spec_clip)
        return {**state, "clip_id": clip_id}
    except Exception as e:  # noqa: BLE001
        return {**state, "error": f"DB storage failed: {e}"}


# -----------------------------
# Graph definition
# -----------------------------


graph_builder = StateGraph(ClipGenerationState)

# Register nodes
graph_builder.add_node("generate_sml_clip", generate_sml_clip)
graph_builder.add_node("store_clip", store_clip)

# Entry point and edges
graph_builder.set_entry_point("generate_sml_clip")
graph_builder.add_edge("generate_sml_clip", "store_clip")
graph_builder.add_edge("store_clip", END)

# Compile graph
clip_graph = graph_builder.compile()


# -----------------------------
# Simple runner for experimentation
# -----------------------------


async def main() -> None:
    """Run the clip generation graph once with a hard-coded prompt.

    Usage:
        export OPENAI_API_KEY=...
        export DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
        python -m src.graphs.clip_graph
    """

    prompt = (
        "Create a 2-bar ascending arpeggio in C major, quarter notes, "
        "ending with a rest."
    )

    state: ClipGenerationState = {"prompt": prompt}
    result = await clip_graph.ainvoke(state)

    print("Final state from LangGraph:")
    import pprint

    pprint.pprint(result)


if __name__ == "__main__":
    asyncio.run(main())
