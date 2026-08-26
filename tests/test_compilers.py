from src.compilers.remotion import compile_remotion_scene_spec, validate_scene_coverage
from src.compilers.framer import compile_framer_contracts, validate_contracts


def _doc():
    return {
      "compiler_targets":{
        "remotion":{"project":{"fps":30,"width":1920,"height":1080,"duration_frames":60},"scene_boundaries":[{"shot_id":"S01","from_frame":0,"to_frame":29},{"shot_id":"S02","from_frame":30,"to_frame":59}],"z_order":["ui","subject","background"]},
        "framer_motion":{"easing_presets":{},"motion_contracts":{}},
      },
      "shots":[
        {"id":"S01","camera_plan":{},"depth_plan":{},"transition_spec":{},"micro_choreography":[]},
        {"id":"S02","camera_plan":{},"depth_plan":{},"transition_spec":{},"micro_choreography":[]},
      ]
    }


def test_remotion_scene_coverage():
    spec=compile_remotion_scene_spec(_doc())
    assert validate_scene_coverage(spec)==[]
    assert [x["durationInFrames"] for x in spec["scenes"]]==[30,30]


def test_framer_required_contracts_are_present():
    compiled=compile_framer_contracts(_doc())
    assert validate_contracts(compiled)==[]
