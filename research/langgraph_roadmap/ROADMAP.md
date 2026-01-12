### Vision: Multi‑agent workflow to convert ideas → structured MIDI clips using your existing tools

> **See also**: 
> - `langgraph_artifacts_catalog.ipynb` - Complete catalog of all nodes/tools with signatures
> - `velocity_humanizer.ipynb` - Detailed implementation example

You already have the right building blocks:
- SML/SMIL AST that supports note timing, velocity, and bar‑level curves for CC, pitch bend, aftertouch, and pedal.
- A facade that orchestrates NL→SML (via LangGraph), SML→DSL, DB I/O, and playback.
- A Fluidsynth player that can schedule CC, velocity curves, and pitch bend.
- A LangGraph “hello world” that generates and stores a clip.

Below is a practical feature/roadmap that turns these into a productive, iterative composer’s assistant with a focus on CC/velocity control.

---

### What LangGraph can do for you here

- Orchestrate an iterative, tool‑driven workflow: generate clip → validate → preview in Fluidsynth → refine (CC/velocity/phrasing) → store → export MIDI.
- Keep state across steps (prompt, SML, DSL, tags, renders, user feedback) and allow branching and retries.
- Encapsulate each operation as a tool: generate, modify, humanize, apply CC templates, change instrument/tuning, render for preview, store/search, export.
- Add guardrails: schema validation, musical constraints (bar lengths, ranges, scales), and safe ranges for MIDI values (0..127; pitch wheel 0..16383 with 8192 center).

---

### Agent roles and graph design

Think of this as an “assistant conductor” with specialists. Each agent has one job and calls your existing code through thin tools.

1) Orchestrator (LangGraph controller)
- Reads user intent, assembles a plan, routes to sub‑agents, tracks state.
- Decides when to loop (e.g., user says “more swing” or “bend first note into the next”).

2) NL→SML Composer
- Uses your existing `src/graphs/clip_graph.py::generate_sml_clip` flow and `OSCFacade.natural_language_clip_to_sml` to produce SML/SMIL.
- Output must pass SML AST validation rules (durations fill bars, pitches 0..127, etc.).

3) SML Validator/Normalizer
- Runs `sml_ast.clip_from_smil_dict` to parse and layout; reports issues: overfull bars, illegal tokens, out‑of‑range velocities, non‑monotonic times in curves.
- Can auto‑fix simple things (round durations to unit grid, clamp velocities/CCs).

4) CC/Velocity Designer (Expression Agent)
- Adds or modifies: velocity curves, mod‑wheel (CC1), expression (CC11), filter (CC74), pitch bend curves, aftertouch, pedal.
- Understands templates and directives like “crescendo over bar 2,” “humanize ±8 velocity with stronger beats on 1 and 3,” “bend the first note into the next note.”

5) Player/Preview Agent
- Calls `OSCFacade.play_clip_from_sml` for instant Fluidsynth preview (no store). Includes loop and tempo overrides via `PlaybackConfig`.

6) DB Librarian
- Calls `OSCFacade.load_dsl_to_db` and `OSCFacade.search_clips` to store and retrieve.
- Attaches tags derived from prompt, key, tempo, mood, and instrument.

7) Exporter
- Calls `OSCFacade.dsl_to_midi_file` to write `.mid` files for import into Reaper.

8) Modifier/Transformer
- Pitch/rhythm ops: transpose, invert, retrograde, swing, quantize, re‑voice.
- Harmony ops: generate chord track from melody; double line an octave below; arpeggiate chord track.

9) QA/Constraint Checker
- Enforces bar completeness, channel ranges, clip key/scale adherence, velocity limits, CC rate limits (no spam), pitch bend range assumptions.

State carried by the graph (example):
- `prompt: str`
- `sml_clip: dict` (bars/items/expression)
- `dsl_clip: dict` (for playback/storage if needed)
- `cc_plan: dict` (high‑level CC directives/templates applied)
- `playback_config: {sf2_path, bpm, loop}`
- `tags: list[str]`
- `clip_id: int | None`
- `export_path: str | None`
- `feedback: str | None`
- `error: str | None`

---

### CC, velocity, pitch‑bend: how to model and use what you already have

Your SML/SMIL and player support expressive data already:
- In `src/dsl/sml_ast.py` you have bar‑level expression fields:
  - `velocity_curve: List[{time, value}]`
  - `cc: Dict[int, List[{time, value}]]` (SML view)
  - `pitch_bend_curve: List[{time, value}]` with 0..16383, 8192 center
  - `aftertouch_curve`, `pedal_events`
- In `src/services/player/midi_builder.py` the player accepts per‑bar:
  - `bar['cc']` as a flat list of `{time, controller, value}` events
  - `bar['velocity_curve']` used to interpolate note velocities
  - `bar['pitch_bend_curve']` and `bar['aftertouch_curve']` sampled during note durations

Design note: if your SML uses `cc` as a dict keyed by controller, add/keep a conversion step in your facade’s SML→DSL to flatten it into the player’s per‑event list. That keeps the authoring format ergonomic while the player format stays simple.

Common CC/velocity workflows to automate:
- Humanization: base velocity by metrical strength + small random jitter
  - Downbeat accent: +12 on beat 1, +6 on beat 3; off‑beats −4..+4 jitter
- Crescendo/diminuendo per bar: set `velocity_curve` like `[{time:0.0,value:70},{time:4.0,value:100}]` for 4/4
- Mod‑wheel swells (CC1): template libraries by instrument (pads/strings/brass)
- Expression (CC11): fine dynamics over the note velocities
- Filter cutoff (CC74): EDM sweeps, risers
- Pedal (CC64): legato piano lines; discrete press/release events
- Pitch bend glides: per the synth pitch bend range (often 2 semitones by default)

Example: “the first note needs to bend into the next note”
- If bar 0 has two notes, N0 at beats [0..1] and N1 at [1..2], create a pitch‑bend curve over N0:
```json
{
  "bars": [
    {
      "bar_index": 0,
      "notes": [
        {"pitch": 60, "start_beat": 0.0, "duration_beats": 1.0},
        {"pitch": 62, "start_beat": 1.0, "duration_beats": 1.0}
      ],
      "pitch_bend_curve": [
        {"time": 0.00, "value": 8192},
        {"time": 0.75, "value": 11000},
        {"time": 1.00, "value": 8192}
      ]
    }
  ]
}
```
- Values are 14‑bit (0..16383), center 8192. Your player maps this to Fluidsynth with `pitch_bend(value - 8192)`.
- For exact glide intervals, either configure pitch‑bend range via RPN (optional future tool), or compute values relative to the default range.

---

### Concrete tools (LangGraph function interfaces) mapped to your code

- `generate_clip_from_nl(prompt) -> sml_clip`
  - Wraps `OSCFacade.natural_language_clip_to_sml` or the existing `clip_graph.generate_sml_clip` function.

- `validate_and_layout(sml_clip) -> {sml_clip, report}`
  - Calls `sml_ast.clip_from_smil_dict` and returns structured errors/warnings.

- `apply_cc_templates(sml_clip, template_id | directives) -> sml_clip`
  - Library: crescendo, tremolo CC1 LFO, pad swell, filter sweep, EDM riser, piano pedal map.

- `humanize_velocities(sml_clip, profile) -> sml_clip`
  - Applies metrical profile + random jitter with bounds; clamps 1..127.

- `apply_pitch_bend(sml_clip, strategy) -> sml_clip`
  - Strategies: glide first‑note→next, blues scoop on pickup, end‑note fall.

- `preview_in_fluidsynth(sml_clip, playback_config) -> {ok: bool}`
  - Wraps `OSCFacade.play_clip_from_sml`.

- `store_clip(sml_clip, tags) -> clip_id`
  - Wraps `OSCFacade.sml_to_dsl_clip` + `ClipService.create_clip_from_dsl`.

- `search_clips(tags | query) -> [dsl_clip]`
  - Wraps `OSCFacade.search_clips`.

- `export_midi(composition_or_clip, options) -> path`
  - Wraps `OSCFacade.dsl_to_midi_file`.

---

### Example LangGraph flows

A) One‑shot Generate → Preview → Store
- Nodes: generate_clip_from_nl → validate_and_layout → apply_cc_templates/humanize → preview_in_fluidsynth → (user feedback?) → store_clip → export_midi
- State: `prompt`, `sml_clip`, `playback_config`, `tags`, `clip_id`, `export_path`

B) Modify Existing Clip (e.g., bend first note)
- Nodes: search_clips → select clip → apply_pitch_bend (directive: “bend first note into next”) → preview → store new version

C) Batch Orchestration
- Nodes: search clips by tag (e.g., “pad”, “bass”, “arp”) → apply instrument‑specific CC templates → align keys/tempi → export multi‑track MIDI project

---

### Opportunities you might be missing

- CC Template Library by instrument family
  - Reusable curves for common articulations (strings swell, brass shake, synth filter sweeps).
- Scale/Key‑Aware Composer
  - Enforce or suggest pitches by scale; automatically transpose clip to project key.
- Groove/Humanize Agent
  - Applies swing, micro‑timing nudges, and beat‑strength velocity patterns.
- Harmonizer Agent
  - From melody, generate chord track; from chords, generate bassline/arp.
- Variation Generator
  - A/B candidate generation; keep top‑K by quick audio preview.
- Critic/QA Agent
  - Objective checks and “explain my clip” summaries; flags MIDI spam (too frequent CC), out‑of‑range pitch bend, overfull bars.
- Retrieval‑Augmented Composition
  - Pull related clips by tags to form arrangements; “compose in the style of my saved ‘lofi‑pads’.”
- Dataset Growth Loop
  - Every approved preview gets stored with rich tags. Over time, prompts + resulting SML become training material for better prompting/templates.

---

### Designing the CC/velocity layer (practical heuristics)

- Metrical profile for velocities (4/4 example):
  - Beat 1: +12, Beat 3: +6, Beats 2 & 4: +2, offbeats: −4..+4 jitter
- Crescendo/diminuendo per bar:
  - `velocity_curve = [{time: 0.0, value: base}, {time: 4.0, value: base+delta}]`
- CC1 (mod wheel) pad swell:
  - `[{time: 0.0, value: 20}, {time: 1.5, value: 90}, {time: 4.0, value: 60}]`
- Aftertouch vibrato:
  - Small periodic modulation: sample 10 points across notes with values ~60–80.
- Pedal mapping for piano:
  - Discrete events: press at phrase start, release at cadences.

These can be produced by the Expression Agent from short English directives or selected templates.

---

### How I’d implement this incrementally (roadmap)

1) Solidify the data contracts
- Confirm/augment SML→DSL conversion so bar‑level `cc` dict becomes the player’s flat `cc` event list.
- Ensure `pitch_bend_curve` values are 0..16383 and center at 8192 throughout the pipeline.

2) Ship the minimum graph for iterative composing
- Graph: generate → validate → preview → store → export
- Tools: wrap existing facade calls; add a simple `humanize_velocities` tool.

3) Expression Agent v1 (velocity + CC templates)
- Implement `apply_cc_templates` (crescendo, swell, filter sweep) and `humanize_velocities`.
- Add “bend first note into next” strategy using bar‑level `pitch_bend_curve`.

4) Library and retrieval
- Add tagging at store time (key, tempo, mood, instrument, prompt hash).
- Expose `search_clips` in the agent UI.

5) Transformers and harmonizer
- Transpose, quantize, swing; add simple harmony generator (triads from scale) or reuse `research/midi.py` helpers as a tool for sketches.

6) QA/critic
- Automated checks, linting, and short textual summaries (what scale, density, dynamic range, CC usage).

7) Multi‑track workflows
- Compose several clips by role (drums, bass, pad, lead); align key/tempo; export combined MIDI.

---

### Concrete next steps you can do today

- Add a thin adapter in your facade (if not already there) to flatten SML `cc` dict → player’s `bar['cc']` event list.
- Create LangGraph tools:
  - `humanize_velocities` and `apply_cc_templates` that operate purely on the SML dict.
  - `preview_in_fluidsynth` to call `OSCFacade.play_clip_from_sml` with `PlaybackConfig`.
- Add a sample “modify” flow: “bend first note into next” → recompute `pitch_bend_curve` → preview.
- Build a small template catalog JSON checked into `src/graphs/cc_templates.json` and load it in the Expression Agent.

If you’d like, I can sketch specific tool function signatures (Python) for the LangGraph nodes and a sample prompt for the Expression Agent so you can plug them into `src/graphs/clip_graph.py`. Would you prefer we start with the velocity humanizer or the CC template applier?