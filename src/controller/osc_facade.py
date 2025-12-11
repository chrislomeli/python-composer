import json
from typing import Any, Dict

from src.controller.osc_models import NLToSMLRequest, NLToSMLResponse, DSLLoadConfig, DSLLoadResult, ClipSearchRequest, \
    ClipDSLResponse, DSLProjectModel, MidiExportOptions, MidiExportResult, PlaybackConfig
from src.dsl.dsl_parser import DSLParser
from src.dsl.sml_ast import clip_from_smil_dict, composition_from_smil_dict
from src.services.clip_service import ClipService
from src.services.composition_service import CompositionService
from src.services.midi_export import composition_db_dict_to_midi_bytes
from src.services.player.midi_player import play_clip


# class NLToSMLRequest(BaseModel):
#     text: str
#
#
# class NLToSMLResponse(BaseModel):
#     sml: Dict[str, Any]
#
#
# class DSLLoadConfig(BaseModel):
#     """Configuration for loading DSL into database."""
#     path: Optional[str] = None
#     dsl_json: Optional[Dict[str, Any]] = None
#
#
# class DSLLoadResult(BaseModel):
#     """Result of loading DSL into database."""
#     composition_id: int
#     clip_ids: List[int] = Field(default_factory=list)
#     composition_name: str
#
#
# class ClipSearchRequest(BaseModel):
#     """Request for searching clips."""
#     tags: Optional[List[str]] = None
#     name_pattern: Optional[str] = None
#
#
# class ClipDSLResponse(BaseModel):
#     """Response containing clip(s) in DSL format."""
#     clips: List[Dict[str, Any]]
#
#
# class DSLProjectModel(BaseModel):
#     project: Dict[str, Any]
#
#
# class MidiExportOptions(BaseModel):
#     """Options controlling how DSL is rendered to MIDI.
#
#     If output_path is provided, the implementation should write a .mid file there.
#     Regardless, in-memory MIDI bytes should be returned in the result object.
#     """
#
#     output_path: Optional[str] = None
#     include_all_tracks: bool = True
#
#
# class MidiExportResult(BaseModel):
#     """Result of rendering DSL/DB data to MIDI.
#
#     midi_bytes contains the raw MIDI file bytes. output_path is set if the
#     implementation wrote a file to disk.
#     """
#
#     midi_bytes: bytes
#     output_path: Optional[str] = None
#
#
# class PlaybackConfig(BaseModel):
#     sf2_path: Optional[str] = None
#     bpm: int = 120
#     loop: bool = False


class OSCFacade:
    """
    Main facade for OSC operations.
    
    Provides high-level operations for:
    - Loading DSL into database
    - Exporting clips/compositions to DSL
    - Converting DSL to MIDI
    - Playback operations
    """
    
    def __init__(self):
        self.clip_service = ClipService()
        self.composition_service = CompositionService()
    
    async def natural_language_clip_to_sml(self, request: NLToSMLRequest) -> NLToSMLResponse:
        """
        Convert natural language prompt to SML clip format using LangGraph.
        
        This proxies to the clip_graph LangGraph implementation which:
        1. Calls OpenAI with structured function calling
        2. Generates SML-style clip JSON
        3. Returns the SML clip (without storing to DB)
        
        Args:
            request: NLToSMLRequest with text prompt
            
        Returns:
            NLToSMLResponse with SML clip dict
            
        Raises:
            ValueError: If graph execution fails or returns error
        """
        from src.graphs.clip_graph import ClipGenerationState
        
        # Initialize graph state with prompt
        state: ClipGenerationState = {"prompt": request.text}
        
        # Run the graph (only the generate_sml_clip node, not storage)
        # We'll invoke just the generation node directly
        from src.graphs.clip_graph import generate_sml_clip
        result = await generate_sml_clip(state)
        
        # Check for errors
        if result.get("error"):
            raise ValueError(f"LangGraph clip generation failed: {result['error']}")
        
        sml_clip = result.get("sml_clip")
        if not sml_clip:
            raise ValueError("No SML clip generated")
        
        return NLToSMLResponse(sml=sml_clip)

    async def natural_language_composition_to_sml(self, request: NLToSMLRequest) -> NLToSMLResponse:
        """
        Convert natural language prompt to SML composition format using LangGraph.
        
        Note: Composition graph not yet implemented. This is a placeholder.
        
        Args:
            request: NLToSMLRequest with text prompt
            
        Returns:
            NLToSMLResponse with SML composition dict
            
        Raises:
            NotImplementedError: Composition graph not yet available
        """
        raise NotImplementedError(
            "Composition graph not yet implemented. "
            "Use natural_language_clip_to_sml() for clip generation, "
            "or create a composition graph similar to clip_graph.py"
        )

    def sml_to_dsl_clip(self, sml_clip: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert SML/SMIL clip format to DSL clip format.
        
        This proxies through to sml_ast.clip_from_smil_dict() and converts
        the resulting Clip AST to spec-compliant DSL format.
        
        Args:
            sml_clip: SMIL-like clip dict with structure:
                {
                    "clip_id": int,
                    "name": str,
                    "track_name": str (optional),
                    "bars": [
                        {
                            "bar_index": int,
                            "items": [
                                {"note": "C4", "duration": "quarter"},
                                {"rest": "quarter"}
                            ],
                            "expression": {...} (optional)
                        }
                    ]
                }
        
        Returns:
            Clip in DSL format (spec-compliant)
        """
        # Convert SMIL to AST Clip
        clip_ast = clip_from_smil_dict(sml_clip)
        
        # Convert AST Clip to spec-compliant DSL format
        return clip_ast.to_spec_clip()

    def sml_to_dsl_composition(self, sml_project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert SML/SMIL composition format to DSL composition format.
        
        This proxies through to sml_ast.composition_from_smil_dict() and converts
        the resulting Composition AST to spec-compliant DSL format.
        
        Args:
            sml_project: SML-style project dict with structure:
                {
                    "project": {
                        "name": str,
                        "ticks_per_quarter": int,
                        "tempo_map": [...],
                        "meter_map": [...],
                        "key_map": [...],
                        "tracks": {
                            "track_name": {
                                "clips": [
                                    {
                                        "clip_instance_id": str,
                                        "clip_id": int,
                                        "start_bar": int,
                                        "length_bars": int
                                    }
                                ]
                            }
                        }
                    }
                }
        
        Returns:
            Composition in DSL format (spec-compliant)
        """
        # Convert SML to AST Composition
        composition_ast = composition_from_smil_dict(sml_project)
        
        # Convert AST Composition to spec-compliant DSL format
        return composition_ast.to_spec_composition()

    async def load_dsl_to_db(self, config: DSLLoadConfig) -> DSLLoadResult:
        """
        Load a complete DSL project into the database.
        
        This orchestrates:
        1. Parse DSL JSON (from file or dict)
        2. Create all clips in database
        3. Create composition with tracks
        
        Args:
            config: DSL load configuration with either path or dsl_json
            
        Returns:
            DSLLoadResult with composition_id and clip_ids
        """
        # Load DSL JSON
        if config.path:
            with open(config.path, 'r') as f:
                dsl_json = json.load(f)
        elif config.dsl_json:
            dsl_json = config.dsl_json
        else:
            raise ValueError("Must provide either path or dsl_json")
        
        # Parse DSL
        parser = DSLParser()
        composition = parser.parse_project(dsl_json)
        db_format = parser.to_database_format(composition)
        
        # Create clips
        clip_ids = []
        for clip_data in db_format["clips"]:
            clip_id = await self.clip_service.create_clip_from_dsl(clip_data)
            clip_ids.append(clip_id)
        
        # Create composition (merge tracks into composition dict)
        comp_data = db_format["composition"]
        comp_data["tracks"] = db_format.get("tracks", [])
        composition_id = await self.composition_service.create_composition_from_dsl(comp_data)
        
        return DSLLoadResult(
            composition_id=composition_id,
            clip_ids=clip_ids,
            composition_name=composition.name
        )

    async def natural_language_clip_to_db(self, request: NLToSMLRequest) -> int:
        """
        Complete pipeline: Natural Language → SML → DSL → Database.
        
        This is a convenience method that combines:
        1. natural_language_clip_to_sml() - NL → SML via LangGraph
        2. sml_to_dsl_clip() - SML → DSL via sml_ast
        3. clip_service.create_clip_from_dsl() - DSL → DB
        
        Args:
            request: NLToSMLRequest with natural language prompt
            
        Returns:
            clip_id of the created clip
            
        Example:
            request = NLToSMLRequest(text="Create a C major scale, quarter notes")
            clip_id = await facade.natural_language_clip_to_db(request)
        """
        # Step 1: NL → SML
        sml_response = await self.natural_language_clip_to_sml(request)
        
        # Step 2: SML → DSL
        dsl_clip = self.sml_to_dsl_clip(sml_response.sml)
        
        # Step 3: DSL → DB
        clip_id = await self.clip_service.create_clip_from_dsl(dsl_clip)
        
        return clip_id

    async def search_clips(self, request: ClipSearchRequest) -> ClipDSLResponse:
        """
        Search for clips by tags or name pattern.
        
        Args:
            request: Search criteria (tags and/or name_pattern)
            
        Returns:
            ClipDSLResponse with matching clips in DSL format
        """
        clips = []
        
        # Search by tags
        if request.tags:
            clips.extend(await self.clip_service.find_clips_by_tags(request.tags))
        
        # Search by name pattern
        if request.name_pattern:
            name_clips = await self.clip_service.find_clips_by_name(request.name_pattern)
            # Get full clip data with bars and notes
            for clip_dict in name_clips:
                full_clip = await self.clip_service.get_clip_with_bars_and_notes(clip_dict["id"])
                if full_clip:
                    clips.append(full_clip)
        
        # Convert to DSL format
        dsl_clips = []
        for clip in clips:
            dsl_clip = self._db_clip_to_dsl(clip)
            dsl_clips.append(dsl_clip)
        
        return ClipDSLResponse(clips=dsl_clips)

    async def clip_to_dsl(self, clip_id: int) -> Dict[str, Any]:
        """
        Retrieve a single clip by ID and return as DSL format.
        
        Args:
            clip_id: ID of the clip
            
        Returns:
            Clip in DSL format
        """
        clip = await self.clip_service.get_clip_with_bars_and_notes(clip_id)
        if not clip:
            raise ValueError(f"Clip {clip_id} not found")
        
        return self._db_clip_to_dsl(clip)

    async def composition_to_dsl(self, composition_id: int) -> DSLProjectModel:
        """
        Retrieve a complete composition and return as DSL project format.
        
        This reconstructs the full DSL structure including:
        - Composition metadata
        - All tracks
        - All referenced clips
        
        Args:
            composition_id: ID of the composition
            
        Returns:
            DSLProjectModel with complete project structure
        """
        # Get composition with tracks
        composition = await self.composition_service.get_composition_with_tracks(composition_id)
        if not composition:
            raise ValueError(f"Composition {composition_id} not found")
        
        # Get all unique clips referenced by tracks
        clip_ids = set()
        for track in composition.get("tracks", []):
            for bar in track.get("bars", []):
                clip_ids.add(bar["clip_id"])
        
        # Load all clips
        clips = []
        for clip_id in clip_ids:
            clip = await self.clip_service.get_clip_with_bars_and_notes(clip_id)
            if clip:
                clips.append(clip)
        
        # Build DSL project structure
        project = {
            "name": composition["name"],
            "ticks_per_quarter": composition.get("ticks_per_quarter", 480),
            "tempo_map": [{"bar": 1, "tempo_bpm": composition.get("tempo_bpm", 120)}],
            "meter_map": [{"bar": 1, "numerator": 4, "denominator": 4}],
            "key_map": [{"bar": 1, "key": "C", "mode": "major"}],
            "tracks": {},
            "clip_library": []
        }
        
        # Add clips to library
        for clip in clips:
            clip_dsl = self._db_clip_to_dsl_library_format(clip)
            project["clip_library"].append(clip_dsl)
        
        # Add tracks
        for track in composition.get("tracks", []):
            track_name = track["name"]
            project["tracks"][track_name] = {
                "instrument": {
                    "name": track_name,
                    "midi_channel": 0
                },
                "clips": []
            }
            
            # Group consecutive bars by clip
            for bar in track.get("bars", []):
                project["tracks"][track_name]["clips"].append({
                    "clip_instance_id": f"{track_name}_{bar['bar_index']}",
                    "clip_id": bar["clip_id"],
                    "start_bar": bar["bar_index"],
                    "length_bars": 1
                })
        
        return DSLProjectModel(project=project)

    def _db_clip_to_dsl(self, clip: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database clip format to DSL clip format."""
        dsl_clip = {
            "clip_id": clip["id"],
            "name": clip["name"],
            "notes": []
        }
        
        if clip.get("track_name"):
            dsl_clip["track_name"] = clip["track_name"]
        
        if clip.get("tags"):
            dsl_clip["tags"] = clip["tags"]
        
        # Flatten notes from bars
        for bar in clip.get("bars", []):
            bar_index = bar["bar_index"]
            for note in bar.get("notes", []):
                note_dict = {
                    "start_beat": note["start_beat"] + (bar_index * 4),
                    "duration_beats": note["duration_beats"]
                }
                
                if note.get("is_rest"):
                    note_dict["is_rest"] = True
                else:
                    note_dict["pitch"] = note["pitch"]
                
                if note.get("articulation"):
                    note_dict["articulation"] = note["articulation"]
                if note.get("dynamics"):
                    note_dict["dynamics"] = note["dynamics"]
                
                dsl_clip["notes"].append(note_dict)
        
        return dsl_clip
    
    def _db_clip_to_dsl_library_format(self, clip: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database clip to DSL clip_library format."""
        return self._db_clip_to_dsl(clip)

    def dsl_to_midi_file(
        self,
        dsl_project: DSLProjectModel,
        options: MidiExportOptions,
    ) -> MidiExportResult:
        # Convert DSL project JSON into a Composition AST and then into
        # a database-style dict that midi_export understands.
        parser = DSLParser()
        dsl_json = {"project": dsl_project.project}
        composition = parser.parse_project(dsl_json)
        db_dict = parser.to_database_format(composition)

        # Render to MIDI bytes.
        midi_bytes = composition_db_dict_to_midi_bytes(
            db_dict,
            include_all_tracks=options.include_all_tracks,
        )

        output_path = options.output_path
        if output_path:
            # Write .mid file to disk.
            with open(output_path, "wb") as f:
                f.write(midi_bytes)

        return MidiExportResult(midi_bytes=midi_bytes, output_path=output_path)

    async def play_clip_from_sml(self, sml_clip: Dict[str, Any], config: PlaybackConfig) -> None:
        """
        Play a clip directly from SML format without storing to database.
        
        This is the workflow for preview/testing before deciding to store.
        
        Pipeline:
        1. Convert SML → DSL (via sml_ast.clip_from_smil_dict)
        2. Play DSL clip (via midi_player.play_clip)
        
        Args:
            sml_clip: SML-style clip dict with structure:
                {
                    "clip_id": int (optional),
                    "name": str,
                    "track_name": str (optional),
                    "bars": [
                        {
                            "bar_index": int,
                            "items": [
                                {"note": "C4", "duration": "quarter"},
                                {"rest": "quarter"}
                            ],
                            "expression": {...} (optional)
                        }
                    ]
                }
            config: PlaybackConfig with sf2_path, bpm, loop settings
            
        Example:
            sml_clip = {"name": "test", "bars": [...]}
            config = PlaybackConfig(bpm=120, loop=False)
            await facade.play_clip_from_sml(sml_clip, config)
        """
        # Step 1: Convert SML → DSL
        dsl_clip = self.sml_to_dsl_clip(sml_clip)
        
        # Step 2: Play DSL clip using midi_player
        play_clip(
            clip_data=dsl_clip,
            sf2_path=config.sf2_path,
            bpm=config.bpm,
            loop=config.loop
        )
    
    async def play_clip_from_nl(self, request: NLToSMLRequest, config: PlaybackConfig) -> NLToSMLResponse:
        """
        Complete workflow: Natural Language → SML → DSL → Play.
        
        This is the main workflow for rapid iteration:
        1. Generate SML from natural language (via LangGraph)
        2. Play the clip immediately (without storing to DB)
        3. Return the SML so you can store it later if you like it
        
        Args:
            request: NLToSMLRequest with natural language prompt
            config: PlaybackConfig with sf2_path, bpm, loop settings
            
        Returns:
            NLToSMLResponse with the generated SML clip
            
        Example:
            request = NLToSMLRequest(text="Create a jazzy bass line in F")
            config = PlaybackConfig(bpm=120, loop=False)
            sml_response = await facade.play_clip_from_nl(request, config)
            
            # If you like it, store it:
            clip_id = await facade.clip_service.create_clip_from_dsl(
                facade.sml_to_dsl_clip(sml_response.sml)
            )
        """
        # Step 1: NL → SML
        sml_response = await self.natural_language_clip_to_sml(request)
        
        # Step 2: Play SML (converts to DSL internally)
        await self.play_clip_from_sml(sml_response.sml, config)
        
        # Step 3: Return SML for optional storage
        return sml_response
    
    async def play_clip(self, clip_id: int, config: PlaybackConfig) -> None:
        """
        Play a clip from the database by ID.
        
        Args:
            clip_id: Database ID of the clip
            config: PlaybackConfig with sf2_path, bpm, loop settings
        """
        # Retrieve clip from DB as DSL
        dsl_clip = await self.clip_to_dsl(clip_id)
        
        # Play using midi_player
        play_clip(
            clip_data=dsl_clip,
            sf2_path=config.sf2_path,
            bpm=config.bpm,
            loop=config.loop
        )

    async def play_composition(self, composition_id: int, config: PlaybackConfig) -> None:
        raise NotImplementedError
