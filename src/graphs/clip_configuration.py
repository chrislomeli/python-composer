GENERATE_CLIP_FROM_NL_SCHEMA = {
    "name": "generate_clip_from_nl",
    "description": "Convert a natural language music instruction into a structured clip AST.",
    "parameters": {
        "type": "object",
        "properties": {
            "clip_name": {"type": "string"},
            "instrument": {"type": "string"},
            "tempo_bpm": {"type": "integer"},
            "bars": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "bar_index": {"type": "integer"},
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "oneOf": [
                                    {
                                        "properties": {
                                            "note": {"type": "string"},   # e.g., "C4"
                                            "duration": {"type": "string"} # e.g., "quarter"
                                        },
                                        "required": ["note", "duration"]
                                    },
                                    {
                                        "properties": {
                                            "rest": {"type": "string"}    # e.g., "quarter"
                                        },
                                        "required": ["rest"]
                                    }
                                ]
                            }
                        },
                        "expression": {"type": "object"}  # optional expression data
                    },
                    "required": ["bar_index", "items"]
                }
            }
        },
        "required": ["clip_name", "instrument", "tempo_bpm", "bars"]
    }
}
