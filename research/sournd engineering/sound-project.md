# Guided Project & Learning Rubric: From Mixed Song to Playable Instrument

This document defines a **structured, from-scratch learning project** for understanding how to extract, analyze, and re-express musical parts from finished recordings as playable instruments.

It is intentionally **methodical, constrained, and progressive**. The goal is not speed or novelty, but *deep, transferable understanding*.

---

## Project Philosophy (Read First)

You are not cloning songs.
You are learning **how sound behaves inside finished music**.

Each stage prioritizes:

* Audible cause-and-effect
* Explainable decisions
* Reusable intuition

Success is defined as **understanding and control**, not fidelity to the original track.

---

## Tooling & Constraints

### Primary Tools

* **Reason DAW** (primary learning environment)
* **Demucs** (external stem separation)
* **Lossless audio purchases** (WAV/FLAC from 7digital or Qobuz)

---

## Deep Dive: Reason-Specific Hybrid Reconstruction Device Chain

[Device chain details as previously defined]

---

## Prerequisites (MacBook Pro, nothing installed)

- [x] macOS up to date, 50–100 GB free
- [x] Reason DAW (standalone)
- [x] Python 3.10+ (via Homebrew)
- [x] Demucs (installed via Python)
- [x] FFmpeg (via Homebrew)
- [x] Audio editor (Audacity or ocenaudio)
- [x] Headphones or monitors
- [x] Folder structure for project
- [x] Lossless music purchases from Qobuz / 7digital
- [x] Optional: third-party stem plugins (for later)
- [x] Optional: advanced resynthesis tools (for later)

---

## Next Steps / Expanded Steps

1. **Exact Install Order with Commands**

   * Homebrew → Python → FFmpeg → Demucs
   * Verify each installation

2. **Recommend First Training Songs**

   * Choose 2–3 bass-heavy or clear-instrument tracks from Qobuz/7digital
   * Prefer simple arrangements for first experiments

3. **Walk Through Demucs → Reason for One Bass Line**

   * Download WAV
   * Run Demucs separation
   * Import stem into Reason
   * Analyze and document envelope, EQ, spatial behavior
   * Rebuild using hybrid chain

4. **Translate Reason Chain into DSP Blocks**

   * Identify: oscillators, filters, envelopes, LFOs, modulation
   * Map to functional DSP primitives
   * Document signal flow

---

### Explicit Constraints (Important)

* One source track at a time
* One musical role at a time (e.g., bass)
* No attempt at perfect reconstruction
* No reliance on presets as explanations

---

## High-Level Learning Phases

1. **Separation** – Obtain usable isolated material
2. **Observation** – Learn to hear and describe sound behavior
3. **Hybrid Re-Expression** – Rebuild behavior using synthesis + shaping
4. **Generalization** – Make the sound playable across pitch
5. **Resynthesis Foundations** – Begin feature-driven sound construction

You only move forward when the *rubric criteria* are met.

---

## Phase 0 — Orientation & Signal Literacy

### Goal

Learn to *listen with intent* and describe sound without jargon or plugins.

### Tasks

* Choose one purchased track you enjoy
* Identify one role (e.g., bass, pad, rhythm guitar)
* Write answers to:

  * Where does this sound sit in frequency?
  * Is it stable or animated?
  * Is it wide or narrow?
  * Does it feel dynamic or controlled?

### Exit Criteria

You can describe the sound in **plain language** without mentioning tools.

---

## Phase 1 — Separation (Demucs)

### Goal

Create a **workable isolated stem** suitable for analysis.

### Tasks

* Run Demucs on the purchased WAV/FLAC
* Export stems in stereo
* Import stems into Reason without normalization

### Listening Focus

* What remains of the target instrument?
* What artifacts exist?
* What musical information survived separation?

### Exit Criteria

You can explain what Demucs preserved and what it destroyed — audibly.

---

## Phase 2 — Sonic Character Analysis (Inside Reason)

### Goal

Identify *what makes the sound feel the way it does*.

### Analysis Dimensions (No Presets)

#### Frequency

* Fundamental range
* Harmonic richness
* Sub vs presence balance

#### Time

* Attack sharpness
* Sustain behavior
* Release length

#### Dynamics

* Perceived compression
* Transient control
* Loudness consistency

#### Space

* Mono vs stereo
* Modulation movement
* Reverb or delay evidence

### Exit Criteria

You can point to a specific moment and say:

> "This quality comes from *this* behavior."

---

## Phase 3 — Hybrid Synthesis (First Instrument)

### Goal

Re-express the sound using **simple synthesis + shaping**, not samples alone.

### Allowed Building Blocks

* Basic oscillator or simple sampled excitation
* Filter + envelope
* Saturation or distortion
* Stereo or modulation effect

### Rules

* One synthesis voice
* No layered stacks
* No impulse responses

### Focus Questions

* What part of the sound comes from excitation?
* What part comes from shaping?
* What part comes from dynamics?

### Exit Criteria

Your instrument:

* Is playable across at least 1 octave
* Resembles the *behavior* of the source
* Responds musically to velocity or envelopes

---

## Phase 4 — Generalization & Chromatic Extension

### Goal

Make the instrument **behave sensibly across pitch**.

### Tasks

* Define pitch-tracking rules (filter, envelopes)
* Prevent low-end stereo chaos
* Adjust envelope scaling by pitch

### Concepts to Learn

* Why real instruments change with pitch
* Why identical envelopes fail
* Why harmonic balance matters more than waveform

### Exit Criteria

The instrument:

* Does not break across 2–3 octaves
* Feels intentionally voiced
* Remains musically usable

---

## Phase 5 — Intro to Resynthesis (Feature-Driven Thinking)

### Goal

Stop thinking in terms of samples and start thinking in **measurable features**.

### Conceptual Shift

From:

> “This sample sounds good”

To:

> “This sound has these controllable properties”

### Early Resynthesis Features

* Spectral envelope
* Harmonic density
* Noise vs tone balance
* Amplitude evolution

### Tasks

* Rebuild the instrument *without* using the stem audio
* Drive parameters from envelopes and modulators
* Compare behavior, not tone

### Exit Criteria

You can explain how the sound is constructed **without referencing the source audio**.

---

## Phase 6 — Reflection & Transfer

### Goal

Ensure the knowledge generalizes beyond one song.

### Tasks

* Apply the same process to a second track
* Identify what stayed the same
* Identify what changed

### Exit Criteria

You can start a new track knowing *where to listen first*.



## What Success Looks Like

* Audible understanding of how instrument behaves
* Ability to rebuild hybrid instrument reproducibly
* Playable across at least 1 octave
* Ready to explore resynthesis confidently
