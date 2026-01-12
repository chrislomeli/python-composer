
# Using Demucs to Extract and Recreate Parts in a DAW
*With recommended plugins for Ableton Live and Reason*

---

## Overview

This document outlines a practical workflow for using **Demucs** to separate stems from a mixed song and then analyze and recreate specific parts (e.g., a “boomy bass line”) inside a DAW such as **Ableton Live** or **Reason**.

---

## 1. Separate Stems with Demucs

1. Install Demucs and choose a high-quality model (e.g., 6-stem or 4-stem).
2. Run separation on your track to export:

- vocals.wav
- bass.wav
- drums.wav
- other.wav


3. Export stems in **stereo** to preserve spatial cues.

---

## 2. Import into Your DAW

1. Import the separated stems into Ableton Live or Reason.
2. Create dedicated tracks for each stem (e.g., bass, drums, vocals).
3. **Do not normalize** the stems unless you intend to analyze relative levels.

---

## 3. Analyze the Isolated Stem

### A. Frequency / EQ Analysis
Use spectrum analyzers to inspect the frequency content.

### B. Stereo Field and Effects
- Check stereo spread (low frequencies should often be more centered)
- Listen for reverb tails or delay repeats — these are part of the stem

### C. Dynamics
- Observe transient behavior to infer compression settings
- Use level meters and waveform views to see peaks vs. RMS

---

## 4. Re-creation in the DAW

### Option A: Reference Approach
- Program MIDI parts that mimic the performance in the bass stem
- Match frequency content and dynamics to the separated audio

### Option B: Use Stem Audio Directly
- Slice the bass stem
- Loop grooves or phrases
- Use them as texture layering under recreated parts

---

## 5. Recommended Plugins for Ableton Live

### 🎛️ Stem / Source Separation Helpers
While Demucs runs outside the DAW, some plugins help with live or realtime isolation as a supplement:

- **Serato Sample 2.0** – AI-powered plugin for slicing stems and performance playback inside your DAW. :contentReference[oaicite:0]{index=0}
- **Acon Digital Remix** – separates audio into multiple parts (vocals, bass, etc.) you can preview and export. :contentReference[oaicite:1]{index=1}

> Note: there aren’t many plugins that do *clean* separation entirely inside a DAW — most heavy stem separation still happens externally (e.g., with Demucs) and then you bring audio back in. :contentReference[oaicite:2]{index=2}

---

### 📊 Analysis & EQ Tools

These help you **measure and match** EQ characteristics of extracted stems.

- **FabFilter Pro-Q 3** – industry standard EQ with visual spectrum and dynamic EQ modes. :contentReference[oaicite:3]{index=3}
- **iZotope Neutron 5** – full mixing suite with spectral analysis and masking meters. :contentReference[oaicite:4]{index=4}
- **Voxengo SPAN** – free spectrum analyzer plugin for detailed frequency inspection. :contentReference[oaicite:5]{index=5}
- **ISOL8 (frequency splitter)** – splits audio into multiple bands for focused processing. :contentReference[oaicite:6]{index=6}

---

### 🥁 Creative & Mixing Plugins

Useful for shaping recreated parts in the DAW:

- **iZotope FXEQ** – creative multi-effect and spectral processing plugin ideal for sculpting parts. :contentReference[oaicite:7]{index=7}
- **Trackspacer (Wavesfactory)** – dynamic EQ sidechains to carve space between parts like bass and kick. :contentReference[oaicite:8]{index=8}

---

## 6. Recommended Tools for Reason

Reason’s Rack and VST support let you use many of the above plugins as VSTs.

- Use **spectrum analyzers** (Voxengo SPAN or stock devices) in Reason’s mixer to view frequency content.
- Load **Pro-Q 3** or **Neutron 5** as VSTs for detailed EQ control.
- Use **ReDrum / Mixer** to integrate separated stems for creative sequencing and re-processing.

---

## 7. Practical Tips

### A. Solo Narrow Frequency Bands
Use a narrow EQ band to solo a frequency slice of the stem to inspect it in detail. This is a common technique for reverse-engineering tracks and learning arrangement characteristics.

### B. Compare with Reference Tracks
Use analyzers and tools like Neutron’s masking meters to see how your recreated parts’ spectrum compares to the isolated stem.

### C. Visual Matching
Pay attention to:
- Peaks from compression
- Bass resonance frequencies
- The “presence” region (2–5 kHz) for definition

---

## Summary

By combining **Demucs separation**, **spectrum analysis**, and DAW plugins like Pro-Q 3, Neutron 5, Voxengo SPAN, and creative tools such as Serato Sample and Trackspacer, you can:
- Extract a part from a mixed song
- Analyze its sonic characteristics
- Recreate or adapt it inside Ableton Live or Reason

This approach blends **AI-powered separation** with **traditional DAW production and analysis** workflows for both learning and creative sampling.

---

