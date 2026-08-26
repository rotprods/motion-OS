from src.extraction.ingest import normalize_ffprobe
from src.extraction.segmentation import detect_shots_from_change_scores
from src.extraction.feature_pack import assemble_feature_pack
from src.normalization.motionstyle import normalize_feature_pack, validate_motionstyle


def test_evidence_bound_normalizer_emits_valid_contract_without_inventing_choreography():
    meta = normalize_ffprobe({"streams":[{"codec_type":"video","avg_frame_rate":"30/1","width":1920,"height":1080,"nb_frames":"30"}],"format":{"duration":"1"}})
    shots = detect_shots_from_change_scores([0.01]*29, fps=30)
    pack = assemble_feature_pack(
        video_meta=meta, shots=shots,
        keyframes=[{"id":"K01","shot_id":"S01","frame":0,"at_ms":0,"sha256":"x"}],
        layout_stats={"pattern":"centered_hero"},
        color_stats={"palette":[{"hex":"#F0F0F0"}]},
        motion_stats={},
        extraction_provenance=[{"module":"fixture","method":"known","version":"1"}],
    )
    doc = normalize_feature_pack(pack)
    validate_motionstyle(doc)
    assert doc["style_system"]["style_family"][0]["id"] == "editorial_minimal"
    assert doc["shots"][0]["micro_choreography"] == []
    assert any("<12 measured steps" in x for x in doc["quality"]["assumptions"])
