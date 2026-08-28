"""Evidence-bound video reverse engineering and reusable editing-template compilation."""

from .action_inventory import (
    ActionInventoryError,
    PeakAdjudication,
    PeakCoverage,
    actions_covering_frame,
    adjudicate_peak,
    detect_local_peaks,
    gauntlet_coverage_from_frame_metrics,
    load_action_inventory,
    peak_coverage,
    validate_action_inventory,
)
from .frame_timeline import FrameTimelineError, compile_frame_timeline, validate_frame_timeline
from .template_compiler import (
    EditingTemplateError,
    build_editing_signature,
    compile_editing_template,
    validate_editing_template,
    write_reverse_engineering_bundle,
)

__all__ = [
    "ActionInventoryError",
    "EditingTemplateError",
    "FrameTimelineError",
    "PeakAdjudication",
    "PeakCoverage",
    "actions_covering_frame",
    "adjudicate_peak",
    "build_editing_signature",
    "compile_editing_template",
    "compile_frame_timeline",
    "detect_local_peaks",
    "gauntlet_coverage_from_frame_metrics",
    "load_action_inventory",
    "peak_coverage",
    "validate_action_inventory",
    "validate_editing_template",
    "validate_frame_timeline",
    "write_reverse_engineering_bundle",
]
