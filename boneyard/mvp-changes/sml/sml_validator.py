# smil_validator.py
from typing import Tuple, Optional, Dict, Any, List
from pydantic import ValidationError
from ast_models import clip_from_smil_dict, smil_bar_from_dict, Clip, Bar

class SMILValidationError(Exception):
    """Wrapper for errors raised during SMIL -> AST conversion/validation."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.details = details

def validate_smil_bar(smil_bar: Dict[str, Any], units_per_bar: int = 32) -> Tuple[Optional[Bar], Optional[SMILValidationError]]:
    """
    Parse a SMIL bar dictionary into an AST Bar and perform layout validation.
    Returns (Bar, None) on success or (None, SMILValidationError) on failure.
    """
    try:
        bar = smil_bar_from_dict(smil_bar, units_per_bar=units_per_bar)
        bar.layout()  # will raise if overflow or invalid durations
        return bar, None
    except (ValueError, ValidationError) as exc:
        return None, SMILValidationError("Bar validation failed", details=str(exc))

def validate_smil_clip(smil_clip: Dict[str, Any], units_per_bar: int = 32) -> Tuple[Optional[Clip], Optional[SMILValidationError]]:
    """
    Parse a SMIL clip dictionary into an AST Clip and perform layout validation for all bars.
    Returns (Clip, None) on success or (None, SMILValidationError) on failure.
    """
    try:
        clip = clip_from_smil_dict(smil_clip, units_per_bar=units_per_bar)
        clip.validate_and_layout()  # will layout all bars and raise on overflow
        return clip, None
    except (ValueError, ValidationError) as exc:
        return None, SMILValidationError("Clip validation failed", details=str(exc))
