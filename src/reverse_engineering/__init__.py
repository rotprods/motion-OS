"""Evidence-bound video reverse engineering and reusable editing-template compilation."""

from .frame_timeline import FrameTimelineError, compile_frame_timeline, validate_frame_timeline
from .template_compiler import (
    EditingTemplateError,
    build_editing_signature,
    compile_editing_template,
    validate_editing_template,
    write_reverse_engineering_bundle,
)

__all__ = [
    "EditingTemplateError",
    "FrameTimelineError",
    "build_editing_signature",
    "compile_editing_template",
    "compile_frame_timeline",
    "validate_editing_template",
    "validate_frame_timeline",
    "write_reverse_engineering_bundle",
]
