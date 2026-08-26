from src.reconstruction.fidelity import timeline_fidelity, choose_encoding


def test_exact_vector_timeline_reports_zero_error():
    frames=[{"f":0,"elements":[{"id":"headline","visible":True,"x":10,"y":20,"w":100,"h":20,"opacity":1,"text_state":{"content":"HELLO"}}]}]
    score=timeline_fidelity(frames, frames)
    assert score["frame_count_exact"] is True
    assert score["text_integrity"] is True
    assert score["id_integrity"] is True
    assert score["mean_state_rmse"] == 0


def test_text_mutation_fails_integrity_and_encoding_policy_prefers_per_frame_for_typing():
    ref=[{"f":0,"elements":[{"id":"t","visible":True,"text_state":{"content":"A"}}]}]
    cand=[{"f":0,"elements":[{"id":"t","visible":True,"text_state":{"content":"B"}}]}]
    assert timeline_fidelity(ref,cand)["text_integrity"] is False
    assert choose_encoding("static", text_typing=True)=="per_frame"
