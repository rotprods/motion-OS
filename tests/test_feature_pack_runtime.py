from src.extraction.ingest import normalize_ffprobe
from src.extraction.segmentation import detect_shots_from_change_scores
from src.extraction.feature_pack import assemble_feature_pack, validate_feature_pack


def test_feature_pack_assembly_validates_against_schema():
    meta = normalize_ffprobe({
        "streams": [{"codec_type":"video","avg_frame_rate":"30/1","width":1080,"height":1920,"codec_name":"h264","nb_frames":"30"}],
        "format": {"duration":"1.0","bit_rate":"1000000"},
    })
    shots = detect_shots_from_change_scores([0.01]*29, fps=30)
    pack = assemble_feature_pack(
        video_meta=meta,
        shots=shots,
        keyframes=[{"id":"K01","shot_id":"S01","frame":0,"at_ms":0,"sha256":"deadbeef"}],
        extraction_provenance=[{"module":"ingest","method":"fixture","version":"1"}],
    )
    validate_feature_pack(pack)
    assert pack["warnings"] == []
    assert pack["video_meta"]["fps_rational"] == [30,1]
