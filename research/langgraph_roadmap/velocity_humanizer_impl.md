### Minimal implementation for `humanize_velocities`

Below is a drop‑in implementation that computes per‑note beat positions by accumulating units according to `DEFAULT_UNITS_PER_BAR` semantics (32 units = whole). It applies the roadmap’s metrical profile (4/4 defaults) and jitter, clamps velocities, and supports simple `crescendo`/`diminuendo` strategies. It operates purely on the SML dict returned by `generate_sml_clip` and does not touch the database.

```python
from __future__ import annotations
from typing import Any, Dict, List, Optional, TypedDict, Literal
import copy
import random

# If available, prefer: from src.dsl.sml_ast import DEFAULT_UNITS_PER_BAR
DEFAULT_UNITS_PER_BAR = 32  # whole note = 32, quarter = 8, eighth = 4, etc.

# Minimal duration token → units map (aligned to DEFAULT_UNITS_PER_BAR)
DURATION_UNIT_MAP = {
    "whole": 32, "half": 16, "quarter": 8, "eighth": 4, "sixteenth": 2, "thirtysecond": 1,
    # Aliases / compact names often seen in prompts
    "1/1": 32, "1/2": 16, "1/4": 8, "1/8": 4, "1/16": 2, "1/32": 1,
}

class HumanizeParams(TypedDict, total=False):
    strategy: Literal["meter_accent", "flat+jitter", "crescendo", "diminuendo"]
    meter: Literal["4/4", "3/4", "6/8"]
    intensity: float
    base_velocity: int
    min_velocity: int
    max_velocity: int
    accent_gain_strong: int
    accent_gain_medium: int
    accent_gain_weak: int
    offbeat_jitter: int
    random_jitter: int
    swing: float
    apply_to_bars: List[int]
    seed: int


def _duration_units(token: str) -> int:
    if token in DURATION_UNIT_MAP:
        return DURATION_UNIT_MAP[token]
    # Fallback: try to parse e.g. "units:4" or numeric string
    if token.startswith("units:"):
        try:
            return max(1, int(token.split(":", 1)[1].strip()))
        except Exception:
            pass
    try:
        return max(1, int(token))
    except Exception:
        raise ValueError(f"Unknown duration token: {token}")


def _beats_per_bar_and_primary(meter: str) -> tuple[int, List[int], List[int]]:
    """Return (beats_per_bar, strong_beats, medium_beats) 1-based indices.
    Weak beats are implied as those not in strong/medium.
    """
    if meter == "3/4":
        return 3, [1], []
    if meter == "6/8":
        # Treat as two dotted quarters: strong on 1, medium on 4
        return 6, [1], [4]
    # default 4/4
    return 4, [1], [3]


def _compute_bar_level_scale(strategy: str, note_idx_in_bar: int, total_notes_in_bar: int) -> float:
    if total_notes_in_bar <= 1:
        return 1.0
    t = note_idx_in_bar / (total_notes_in_bar - 1)  # 0..1 across the bar
    if strategy == "crescendo":
        return 0.7 + 0.6 * t  # 0.7..1.3
    if strategy == "diminuendo":
        return 1.3 - 0.6 * t  # 1.3..0.7
    return 1.0


def humanize_velocities(
    sml_clip: Dict[str, Any],
    params: Optional[HumanizeParams] = None,
) -> Dict[str, Any]:
    """Return a new SML clip dict with humanized note velocities.

    - Computes per-note beat positions inside each bar using duration units.
    - Applies metrical accents, offbeat and random jitter, and optional
      crescendo/diminuendo scaling.
    - Clamps velocities to the configured range.
    - Pure function over the SML dict (returns a deep copy).
    """
    p: HumanizeParams = {
        "strategy": "meter_accent",
        "meter": "4/4",
        "intensity": 0.5,
        "base_velocity": 90,
        "min_velocity": 20,
        "max_velocity": 120,
        "accent_gain_strong": 12,
        "accent_gain_medium": 6,
        "accent_gain_weak": 2,
        "offbeat_jitter": 4,
        "random_jitter": 3,
        "swing": 0.0,
        **(params or {}),
    }

    if "seed" in p and isinstance(p["seed"], int):
        random.seed(p["seed"])  # deterministic runs when requested

    beats_per_bar, strong_beats, medium_beats = _beats_per_bar_and_primary(p.get("meter", "4/4"))
    beat_unit = DEFAULT_UNITS_PER_BAR // beats_per_bar  # e.g., 8 for 4/4

    out = copy.deepcopy(sml_clip)

    bars = out.get("bars", [])
    apply_to = set(p.get("apply_to_bars", [])) if p.get("apply_to_bars") else None

    for bar in bars:
        bar_index = int(bar.get("bar_index", 1))
        if apply_to is not None and bar_index not in apply_to:
            # Respect base velocities; skip this bar
            continue

        items: List[Dict[str, Any]] = bar.get("items", [])

        # Build a list of note indices for bar-level scaling (exclude rests)
        note_positions = [i for i, it in enumerate(items) if "note" in it]
        total_notes = len(note_positions)
        note_counter = 0

        # Iterate with a running position in units to find beat positions
        pos_units = 0
        for i, it in enumerate(items):
            # Determine item units to advance pos regardless of type
            units = 0
            if "duration" in it:
                try:
                    units = _duration_units(str(it["duration"]))
                except Exception:
                    units = beat_unit  # fail-safe default: quarter note in 4/4

            if "rest" in it and "duration" not in it:
                # Some payloads might only specify rest token under 'rest'
                units = _duration_units(str(it["rest"]))

            if "note" not in it:
                # Not a note → just advance time and continue
                pos_units += units
                continue

            # Compute beat index (1..beats_per_bar) for note onset
            beat_index_1b = int(pos_units // beat_unit) + 1
            if beat_index_1b < 1:
                beat_index_1b = 1
            if beat_index_1b > beats_per_bar:
                beat_index_1b = beats_per_bar

            # Determine on/off-beat: on-beat if aligns with beat boundary
            on_beat = (pos_units % beat_unit) == 0

            # Base and deltas
            base_v = int(it.get("velocity", p["base_velocity"]))
            delta = 0.0

            # Strategy: meter accents vs flat
            strategy = p.get("strategy", "meter_accent")
            intensity = float(p.get("intensity", 0.5))

            if strategy in ("meter_accent", "flat+jitter"):
                if strategy == "meter_accent":
                    if beat_index_1b in strong_beats:
                        delta += p["accent_gain_strong"]
                    elif beat_index_1b in medium_beats:
                        delta += p["accent_gain_medium"]
                    else:
                        delta += p["accent_gain_weak"]

                # Offbeat jitter (more noticeable away from downbeats)
                if not on_beat and p["offbeat_jitter"] > 0:
                    delta += random.randint(-p["offbeat_jitter"], p["offbeat_jitter"])  # noqa: S311

            # Random jitter always slightly present (if configured)
            rjit = int(p.get("random_jitter", 0))
            if rjit > 0:
                delta += random.randint(-rjit, rjit)  # noqa: S311

            # Apply bar-level scaling for cresc/decresc
            scale = _compute_bar_level_scale(strategy, note_counter, total_notes)
            note_counter += 1

            # Apply intensity and scaling
            v = base_v + int(round(delta * intensity))
            v = int(round(v * scale))

            # Clamp
            v = max(int(p["min_velocity"]), min(int(p["max_velocity"]), v))

            it["velocity"] = v

            # Advance position by this note's duration
            pos_units += units

    return out
```

---

### LangGraph node wrapper (unchanged signature, now calls the implementation)
```python
async def apply_velocity_humanization(state: ClipGenerationState) -> ClipGenerationState:
    if state.get("error"):
        return state

    sml = state.get("sml_clip")
    if not sml:
        return {**state, "error": "No sml_clip in state for velocity humanization"}

    params: HumanizeParams = state.get("humanize_params", {})  # type: ignore
    try:
        updated = humanize_velocities(sml, params)
        return {**state, "sml_clip": updated}
    except Exception as e:
        return {**state, "error": f"Velocity humanization failed: {e}"}
```

---

### Sensible defaults you can pass from `main()` for a quick audible win
```python
humanize_params: HumanizeParams = {
    "strategy": "meter_accent",
    "meter": "4/4",
    "intensity": 0.55,
    "base_velocity": 88,
    "min_velocity": 20,
    "max_velocity": 120,
    "accent_gain_strong": 12,
    "accent_gain_medium": 6,
    "accent_gain_weak": 2,
    "offbeat_jitter": 4,
    "random_jitter": 3,
    "seed": 42,
}
```

This should align closely with the “Designing the CC/velocity layer” section from your `ROADMAP.md` and is easy to tweak. If you’d like, I can follow up with a tiny unit-style check that prints before/after velocities per bar for a given prompt, or move on to the CC template applier next.