from typing import Any, Dict, Optional, List

from pydantic import BaseModel, Field


class NLToSMLRequest(BaseModel):
    text: str


class NLToSMLResponse(BaseModel):
    sml: Dict[str, Any]


class DSLLoadConfig(BaseModel):
    """Configuration for loading DSL into database."""
    path: Optional[str] = None
    dsl_json: Optional[Dict[str, Any]] = None


class DSLLoadResult(BaseModel):
    """Result of loading DSL into database."""
    composition_id: int
    clip_ids: List[int] = Field(default_factory=list)
    composition_name: str


class ClipSearchRequest(BaseModel):
    """Request for searching clips."""
    tags: Optional[List[str]] = None
    name_pattern: Optional[str] = None


class ClipDSLResponse(BaseModel):
    """Response containing clip(s) in DSL format."""
    clips: List[Dict[str, Any]]


class DSLProjectModel(BaseModel):
    project: Dict[str, Any]


class MidiExportOptions(BaseModel):
    """Options controlling how DSL is rendered to MIDI.

    If output_path is provided, the implementation should write a .mid file there.
    Regardless, in-memory MIDI bytes should be returned in the result object.
    """

    output_path: Optional[str] = None
    include_all_tracks: bool = True


class MidiExportResult(BaseModel):
    """Result of rendering DSL/DB data to MIDI.

    midi_bytes contains the raw MIDI file bytes. output_path is set if the
    implementation wrote a file to disk.
    """

    midi_bytes: bytes
    output_path: Optional[str] = None


class PlaybackConfig(BaseModel):
    sf2_path: Optional[str] = None
    bpm: int = 120
    loop: bool = False

