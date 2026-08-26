from src.core.semantic_behavior import compile_semantic_behaviors, primitive_candidates
from src.core.motion_system import compile_motion_system, compile_scene_contracts
from src.qa.grammar_critic import score_grammar, enforce_primitive_route
from src.reconstruction.svg_player import emit_svg_js_player


def test_semantics_compile_before_primitives_and_scene_contracts():
    behaviors=compile_semantic_behaviors("Autonomy removes the bottleneck and improves productivity")
    names={b.behavior for b in behaviors}
    assert {"controller_node","geometric_narrowing","parallel_branching"} <= names
    system=compile_motion_system(brief="autonomy and focus", grammar={"primitives":["node_expand","focus_lock"],"negatives":["random_glitch"]})
    assert system["semantic_behaviors"][0]["behavior"]=="controller_node"
    scenes=compile_scene_contracts(system,[{"id":"S01","objective":"show autonomy"}])
    assert scenes[0]["grammar_constraints"]["one_dominant_idea"] is True


def test_grammar_critic_has_hard_text_gate_and_route_enforcement():
    obs={k:1.0 for k in ["hierarchy_under_motion","beat_focus","motion_intent","transition_motivation","product_ui_authenticity","material_consistency","audio_visual_sync","final_hold_stability","text_integrity"]}
    assert score_grammar(obs)["passed"] is True
    obs["text_integrity"]=0.8
    assert score_grammar(obs)["passed"] is False
    assert enforce_primitive_route(["glitch"],allowed=["slide"],forbidden=["glitch"])["passed"] is False


def test_svg_player_emits_stable_ids_and_timeline_payload():
    recon={
      "SVG_FRAME_RECON_PLAN":{"meta":{"fps":30}},
      "SVG_ASSET_MAP":{"canvas":{"width":100,"height":100,"viewBox":"0 0 100 100"},"elements":[{"id":"t","type":"text","vectorizable":True,"text_state":{"content":"HELLO"}}]},
      "SVG_TIMELINE_FRAME_DATA":{"fps":30,"total_frames":1,"frame_data":[{"f":0,"elements":[{"id":"t","visible":True,"x":10,"y":20,"opacity":1,"transform":{"translate":[0,0],"scale":[1,1],"rotate":0},"text_state":{"content":"HELLO"}}]}]}
    }
    html=emit_svg_js_player(recon)
    assert 'id="t"' in html
    assert 'window.MOTION_OS' in html
    assert 'HELLO' in html
