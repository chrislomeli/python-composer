# OSC Code Review (src/)

## Scope

- **Scope covered**: `src/` package in this repo, including `api`, `controller`, `core`, `dsl`, `graphs`, `repository`, `services`, and `services/player`.
- **Out of scope**: `boneyard/`, `research/`, `songs/`, and non-src tooling. Test files are noted but not deeply reviewed.

The goal is to assess **design cohesion**, **professionalism**, and **code smells**, and to identify **files that appear to be dead code** (not referenced anywhere in the active code paths).

---

## High-Level Architecture & Cohesion

- **Layering**
  - **API layer**: `src/api/app.py` and `src/api/facade_endpoints.py` expose FastAPI endpoints.
  - **Facade/controller layer**: `src/controller/osc_facade.py` provides a rich orchestration facade around services, DSL, and playback.
  - **Service layer**: `src/services/clip_service.py`, `src/services/composition_service.py`, `src/services/midi_export.py` encapsulate async DB operations and business logic.
  - **Repository layer**: `src/repository/*` implements data access on top of SQLAlchemy Core schema in `src/core/schema.py`.
  - **Domain/DSL layer**: `src/core/models.py`, `src/dsl/*`, and `src/graphs/*` handle DSL structures, parsing, and LangGraph integration.
  - **Playback utilities**: `src/services/player/midi_builder.py` and `src/services/player/midi_player.py` handle real-time MIDI playback via mido/FluidSynth.

- **Cohesion & style**
  - Overall, the design is **cohesive and layered**. The responsibilities of API → facade → services → repositories → DB are clear and consistently applied.
  - Pydantic models and SQLAlchemy tables are well-aligned with the spec (Note/Clip/Composition, etc.).
  - Asynchronous database access is consistently used in services and repositories.
  - There is good documentation density (docstrings and Markdown docs like `DSL.md`, `FACADE_USAGE.md`, `API_USAGE.md`).

- **Minor cohesion issues**
  - There are **two “front doors”**:
    - `src/api/app.py` ("OSC MVP API").
    - `src/api/app_with_facade.py` (enhanced version that composes original and facade endpoints).
    - This is fine for now, but for a professional release you will likely want **one canonical app module** and clearly mark the other as legacy or example.
  - The playback path is split:
    - `OSCFacade` imports `play_clip` from `src.services.player.midi_player` and 
    - `MidiClipPlayer` is in `src/services/player/midi_builder.py`.
    - The naming and separation are reasonable, but the **test/demo code in `midi_player.py` blurs the boundary** between library and script (see details below).

---

## Package-by-Package Notes & Code Smells

### 1. `src/api`

**Files reviewed**: `app.py`, `app_with_facade.py`, `facade_endpoints.py`, `API_USAGE.md`, `payloads/*`, tests.

- **Strengths**
  - Clear, well-typed FastAPI endpoints with Pydantic request models.
  - Dependency injection for `ClipService` and `CompositionService` is idiomatic.
  - `facade_endpoints.py` reuses the facade’s Pydantic models directly, which keeps types in sync.
  - `app_with_facade.py` nicely composes both legacy and facade routers.

- **Smells / improvement points**
  - **Duplicate app entrypoints**: `app.py` vs `app_with_facade.py`. For production, pick one and treat the other as:
    - A clearly documented example (`*_example.py`), or
    - A deprecated/legacy module.
  - **Payload files under `api/payloads`**:
    - `create_composition.json.py` is **JSON content with a `.py` extension**. This is confusing and non-standard.
      - Suggestion: rename to `create_composition.json` or `create_composition_example.json`.

### 2. `src/controller`

**Files reviewed**: `osc_facade.py`, `FACADE_USAGE.md`, tests.

- **Strengths**
  - `OSCFacade` provides a **very clear orchestration boundary** between API and lower layers.
  - Pydantic models for facade requests/responses are explicit and self-documenting.
  - Methods like `natural_language_clip_to_db`, `load_dsl_to_db`, `composition_to_dsl`, and `dsl_to_midi_file` are very cohesive and readable.
  - Good use of LangGraph integration (`clip_graph`) is encapsulated inside facade, not leaking into API.

- **Smells / improvement points**
  - **Size / monolith**: `osc_facade.py` is ~600 lines and mixes:
    - Pydantic schemas.
    - Facade orchestration methods.
    - Private conversion helpers.
    - Playback operations.
    - Consider splitting into submodules:
      - `osc_facade_models.py` (Pydantic schemas).
      - `osc_facade_core.py` (DB/DSL orchestration).
      - `osc_facade_playback.py` (playback-related methods).
  - **NotImplemented placeholder**:
    - `play_composition` and `natural_language_composition_to_sml` raise `NotImplementedError`. That’s fine for an alpha, but for professional polish:
      - Either implement or
      - Document them clearly as future work in the docstring and possibly hide them from public API.
  - **Tight coupling to playback implementation**:
    - `OSCFacade` directly imports and invokes `play_clip` from `midi_player` (which in turn instantiates `MidiClipPlayer`).
    - For testability and flexibility, consider **inverting this dependency** via a playback interface/protocol that can be mocked or swapped (e.g., `PlaybackPort` or `PlaybackBackend`).

### 3. `src/core`

**Files reviewed**: `models.py`, `schema.py`, `__init__.py`.

- **Strengths**
  - Domain models (`Note`, `ClipBar`, `Clip`, `TrackBarRef`, `Track`, `Composition`) are clear, spec-aligned, and use Pydantic effectively.
  - `schema.py`’s SQLAlchemy Core tables match the domain nicely and use indexes appropriately.
  - `core.__init__` cleanly exports the main models and tables.

- **Smells / improvement points**
  - `Note` validator forbids `absolute_pitch` when `is_rest` is true. This is **semantically nice**, but you’ll want to ensure every code path constructing notes respects that (right now, `clip_service` reads `absolute_pitch` from DSL and passes to DB directly). In practice this doesn’t seem to be used at scale yet; just be aware of this constraint.
  - `TrackBarRef` and `Track` currently model references by embedding `Clip`, whereas DB tables use `clip_id` and `clip_bar_index`. This is fine as a spec model, but you may eventually need explicit conversion utilities between DB dictionaries and these Pydantic models to keep the mental model consistent throughout the stack.

### 4. `src/dsl`

**Files reviewed**: `__init__.py`, `dsl_parser.py`, `sml_ast.py`, `DSL.md`, `GLOSSARY.md`, `README.md`, examples & tests.

- **Strengths**
  - Documentation in `DSL.md`, `GLOSSARY.md`, and `README.md` is strong and professional.
  - `dsl_parser.py` and `sml_ast.py` are clearly written and extensively tested (`dsl/tests/test_dsl_parser.py`).
  - `__init__.py` exposes `DSLParser` and core AST classes succinctly.

- **Smells / improvement points**
  - No major structural smells here; the DSL layer is well-contained. The main suggestion is to ensure **public API of `dsl` is stable** and re-exported in `__all__` if you want consumers to rely on it.

### 5. `src/graphs`

**Files reviewed**: `clip_configuration.py`, `clip_graph.py`.

- **Strengths**
  - Clean separation of LangGraph-related configuration from the main business logic.
  - `clip_graph` is referenced from `OSCFacade` and appears to be the only active graph entrypoint.

- **Smells / improvement points**
  - None major from a design perspective. Just ensure tests keep pace so graph changes don’t silently break the facade.

### 6. `src/repository`

**Files reviewed**: `__init__.py`, `database.py`, `base_repository.py`, `clip_repository.py`, `clip_bar_repository.py`, `note_repository.py`, `composition_repository.py`, `track_repository.py`, `track_bar_repository.py`, `login.py`.

- **Strengths**
  - Repositories are well-factored by aggregate (`ClipRepository`, `CompositionRepository`, etc.) and cleanly import from `core.schema`.
  - `database.py` + `get_database`/`reset_database` give you a good abstraction for tests (used in `services/tests/test_clip_service.py`).
  - `repository.__init__` provides a convenient aggregated import surface for services.

- **Smells / improvement points**
  - **`login.py` appears dead**:
    - Defines `DatabaseLogin` with `toURL()`, but grep shows no usage under `src/`.
    - The current DB configuration uses `DATABASE_URL` and `get_database` instead.
    - This looks like an early experiment or a remnant. See “Dead Code Files” section.

### 7. `src/services`

**Files reviewed**: `__init__.py`, `clip_service.py`, `composition_service.py`, `midi_export.py`, `bootstrap_db.py`, `player/*`, tests.

- **Strengths**
  - `ClipService` and `CompositionService` are **clean, async, and focused on orchestration** of repository calls.
  - `midi_export.py` is well-structured, with `composition_db_dict_to_midi_bytes` and a clearly separated interpolation helper.
  - `bootstrap_db.py` is a simple and practical utility for initialising DB tables.
  - `services.__init__` exports services nicely.

- **Smells / improvement points**
  - **`midi_player.py` mixing library and script**:
    - `play_clip()` is a useful function and is imported by `OSCFacade`.
    - The bottom `if __name__ == "__main__":` block contains a hard-coded JSON string and an absolute SoundFont path pointing to your local machine.
    - For a professional solution:
      - Move this usage example to a dedicated `examples/` directory or a `README` snippet.
      - Keep `midi_player.py` purely as a library module.
  - **`test-fluid.py` is a one-off environment probe** for FluidSynth dynamic library paths. It is not referenced anywhere.
    - This is fine for local experiments, but in a polished repo it should either live under `boneyard/`, `research/`, or be removed.
  - **`services/tests` are good but incomplete**:
    - `test_clip_service.py` exists and is robust.
    - There is no analogous `test_composition_service.py` in `services/tests` (tooling reported missing file). If it was deleted intentionally, you’re fine; otherwise adding tests for compositions would improve coverage and symmetry.

---

## Candidate Dead Code Files

> Definition here: files in `src/` that are **not imported or referenced by any other active code paths**, and that appear to be remnants or local experiments rather than part of the intended surface area.

Based on repo-wide searches (excluding `boneyard/` and `research/` which are explicitly archival), these are the main candidates:

1. **`src/repository/login.py`**
   - **What it is**: A simple Pydantic model `DatabaseLogin` with a `toURL()` helper to build a Postgres DSN.
   - **Usage**: No references found in `src/` (DB configuration is done via `DATABASE_URL` and `database.py`).
   - **Assessment**: Appears to be an early experiment or unused helper.
   - **Suggestion**: Either
     - Move to `boneyard/` or a `legacy/` area, or
     - Delete it to reduce confusion.

2. **`src/services/player/test-fluid.py`**
   - **What it is**: A stand-alone script using `ctypes` to probe FluidSynth installation paths on macOS (printing success/failure of `LoadLibrary`).
   - **Usage**: No imports or references from the rest of the code.
   - **Assessment**: Purely a local environment check; not part of the application logic.
   - **Suggestion**: Move under `boneyard/`/`research/` or remove once FluidSynth integration is stable.

3. **`src/api/payloads/create_composition.json.py`**
   - **What it is**: A JSON example payload with a `.py` extension (not valid Python code, just a JSON object literal).
   - **Usage**: No references from code. Likely used manually as an example body for HTTP requests.
   - **Assessment**: Functionally dead from Python’s perspective, but **useful as documentation**.
   - **Suggestion**: Rename to `create_composition.json` or `create_composition_example.json` so that tools and readers recognize it as data, not code. Keep it if you find it useful for manual API testing.

4. **`src/tools/` directory**
   - **What it is**: Currently empty.
   - **Usage**: None.
   - **Assessment**: Reserved namespace. Not harmful, but it can confuse readers.
   - **Suggestion**: Either populate with actual tools or remove/ignore it until needed.

5. **`src/services/player/README.txt` and `copyright.txt`**
   - These are documentation/license artifacts for the SoundFont or playback environment. They are not dead “code” per se and can remain, but they don’t participate in the Python dependency graph.

No other `.py` modules under `src/` stood out as entirely dead—everything else is either imported, referenced by tests, or obviously part of the active architecture (API, facade, services, DSL, repositories, graphs).

---

## Professionalism & Style Suggestions

- **Unify entrypoints & configs**
  - Decide on one canonical FastAPI app (`app.py` vs `app_with_facade.py`) for production.
  - Make sure docs point consistently to that entrypoint (and consider a single `uvicorn` command in a top-level README).

- **Clarify experimental vs production modules**
  - Move clearly experimental or environment-probing scripts (`test-fluid.py`, possibly some payload files) into an `examples/`, `scripts/`, or `boneyard/` folder outside of `src/`.
  - This keeps `src/` purely for production code.

- **Module decomposition for `osc_facade.py`**
  - As `OSCFacade` grows, split models/helpers/playback into smaller, focused modules to keep each file readable and to make unit testing more targeted.

- **Configuration & paths**
  - Eliminate hard-coded absolute paths (e.g., SF2 path in `midi_player.py` example). For examples, prefer environment variables or project-relative paths, and clearly document them instead.

- **Testing**
  - You already have:
    - `dsl/tests/test_dsl_parser.py`
    - `services/tests/test_clip_service.py`
    - `controller/tests/test_osc_facade.py`
    - `api/tests/test_facade_api.py`
  - Consider adding mirrored tests for compositions (service + facade + API), and a minimal playback smoke test (behind a feature flag or mocked backend) once playback solidifies.

---

## Summary

- The solution is **already quite professional and cohesive**:
  - Clear multi-layer architecture (API → facade → services → repositories → DB/DSL).
  - Strong documentation and Pydantic type usage.
  - Good early test coverage on key layers.
- Main opportunities to increase polish:
  - Trim or relocate **dead/experimental files** (`repository/login.py`, `services/player/test-fluid.py`, odd `.json.py` files).
  - Normalize **entrypoints and playback configuration** for a clean production story.
  - Gradually **modularize large orchestration modules** (especially `osc_facade.py`).

If you’d like, the next step can be a targeted cleanup PR where we:
- Move or delete the identified dead-code files.
- Normalize payload example filenames.
- Extract `osc_facade` models/helpers into submodules without changing behavior.
