from src.knowledge.style_store import connect, upsert_style_signature, retrieve_similar
from src.qa.gauntlet_v2 import evaluate_verticals, promotion_decision, learning_delta


def test_style_store_retrieves_nearest_signature():
    conn=connect()
    upsert_style_signature(conn,signature_id="a",source_id="v1",style_family="minimal_orbit",payload={"x":1},vector=[1,0],evidence_coverage=.9)
    upsert_style_signature(conn,signature_id="b",source_id="v2",style_family="portal_glass_ui",payload={"x":2},vector=[0,1],evidence_coverage=1)
    result=retrieve_similar(conn,[.9,.1],limit=1)
    assert result[0]["id"]=="a"


def test_gauntlet_refuses_fixture_only_creative_promotion():
    scores={k:1.0 for k in ["extraction","evidence","normalization","compiler","reconstruction","grammar","creative","operations"]}
    evidence={k:["artifact:1"] for k in scores}
    authority={k:"authoritative" for k in scores}
    authority["creative"]="fixture"
    results=evaluate_verticals(scores,evidence=evidence,authority=authority)
    decision=promotion_decision(results)
    assert decision["decision"]=="HOLD"
    assert "creative" in decision["failed_verticals"]


def test_learning_delta_tracks_regression():
    d=learning_delta({"motion":.8,"type":.9},{"motion":.9,"type":.85})
    assert d["improved"]==["motion"]
    assert d["regressed"]==["type"]
