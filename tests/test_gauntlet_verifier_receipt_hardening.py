import pytest

from scripts.gauntlet_loop import GauntletError, evaluate_gauntlet


def _attempt(result_hash: str):
    return [{
        "iteration": 1,
        "strategy": "repair authority boundary",
        "result_hash": result_hash,
        "verifier_complete": True,
        "verifier_reason": "all bounded invariants pass",
        "measurable_progress": 1.0,
    }]


def _receipt(result_hash: str):
    return {
        "implementer_id": "motion://agent/implementer/1",
        "verifier_id": "motion://agent/verifier/1",
        "verified_result_hash": result_hash,
        "evidence_hash": "e" * 64,
        "decision": "PASS",
    }


@pytest.mark.parametrize("field,bad", [
    ("implementer_id", None),
    ("implementer_id", True),
    ("verifier_id", None),
    ("verifier_id", 7),
])
def test_verifier_identity_type_confusion_fails_closed(field, bad):
    result_hash = "a" * 64
    receipt = _receipt(result_hash)
    receipt[field] = bad
    with pytest.raises(GauntletError, match="identity"):
        evaluate_gauntlet(_attempt(result_hash), verifier_receipt=receipt)


def test_verifier_receipt_requires_real_sha256_shaped_strings():
    result_hash = "a" * 64
    receipt = _receipt(result_hash)
    receipt["evidence_hash"] = True
    with pytest.raises(GauntletError, match="evidence_hash"):
        evaluate_gauntlet(_attempt(result_hash), verifier_receipt=receipt)
