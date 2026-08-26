from pathlib import Path
import hashlib

from PIL import Image

from src.core.reference_conditioning import apply_reference_conditioning, build_reference_conditioning
from src.core.motion_system import compile_motion_system, compile_scene_contracts
from src.reconstruction.raster_sequence import build_raster_sequence_timeline, emit_raster_sequence_player, verify_raster_records


def test_reference_conditioning_is_soft_and_provenance_bound():
    neighbors=[{
        "source_id":"ref:001","style_family":"minimal_orbit","similarity":.91,"evidence_coverage":.88,
        "payload":{"style_system":{"color":{"background":["#EFEFED"]},"typography":{"role":"minimal"},"composition":{"pattern":"centered"},"motion":{"energy":"low"},"materials_3d":["matte_plastic"],"fx":["soft_shadow"]}}
    }]
    conditioning=build_reference_conditioning(neighbors)
    assert conditioning["authority"] == "retrieved_evidence_soft_constraint"
    assert conditioning["forbidden_copy"] is True
    style=apply_reference_conditioning({},conditioning)
    system=compile_motion_system(brief="autonomous system",style_doc=style)
    assert system["provenance"]["reference_source_ids"] == ["ref:001"]
    assert system["provenance"]["forbidden_copy"] is True
    scenes=compile_scene_contracts(system,[{"id":"S01","text":"Autonomy"}])
    assert scenes[0]["reference_constraints"]["forbidden_copy"] is True


def test_low_authority_references_do_not_condition():
    c=build_reference_conditioning([{"source_id":"x","similarity":.2,"evidence_coverage":1,"payload":{}}])
    assert c["authority"] == "none"
    assert c["sources"] == []


def test_raster_sequence_reconstruction_is_hash_locked(tmp_path: Path):
    records=[]
    for i,color in enumerate([(0,0,0),(255,255,255),(120,40,20)]):
        p=tmp_path/f"{i}.png"
        Image.new("RGB",(64,36),color).save(p)
        records.append({"frame":i,"path":str(p),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    assert verify_raster_records(records) == []
    tl=build_raster_sequence_timeline(records,fps=30,width=64,height=36)
    assert tl["total_frames"] == 3
    assert tl["fidelity_claim"].startswith("decoded_frame_sequence")
    assert len(tl["timeline_sha256"]) == 64
    html=emit_raster_sequence_player(tl)
    assert "motionOS" in html and "setFrame" in html
    # A changed source frame must invalidate evidence.
    Image.new("RGB",(64,36),(1,2,3)).save(tmp_path/"1.png")
    assert any(x.startswith("sha_mismatch") for x in verify_raster_records(records))
