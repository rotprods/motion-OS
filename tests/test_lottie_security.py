import math

import pytest

from src.compilers.lottie import (
    compile_vector_subgraph_to_lottie,
    validate_lottie_subset,
)


def _image_doc(asset):
    return compile_vector_subgraph_to_lottie(
        [
            {
                "id": "image-layer",
                "type": "image",
                "features": ["transform"],
                "data": {"ref_id": "asset-1"},
            }
        ],
        width=640,
        height=360,
        fps=30,
        out_frame=30,
        assets=[asset],
    )


@pytest.mark.parametrize(
    "asset",
    [
        {"id": "asset-1", "u": "https://attacker.invalid/", "p": "image.png"},
        {"id": "asset-1", "u": "../outside/", "p": "image.png"},
        {"id": "asset-1", "u": "", "p": "file:///tmp/secret.png"},
        {"id": "asset-1", "u": "", "p": "data:image/svg+xml,<svg/>"},
    ],
)
def test_lottie_compiler_rejects_remote_or_escaping_asset_locations(asset):
    with pytest.raises(ValueError, match="Unsupported Lottie subset"):
        _image_doc(asset)


def test_lottie_compiler_accepts_local_relative_asset_location():
    doc = _image_doc({"id": "asset-1", "u": "images/", "p": "hero.png"})
    assert validate_lottie_subset(doc).supported is True


def test_lottie_validation_rejects_nonfinite_numeric_payloads():
    doc = {
        "v": "5.12.0",
        "fr": math.nan,
        "ip": 0,
        "op": 30,
        "w": 640,
        "h": 360,
        "assets": [],
        "layers": [],
    }
    validation = validate_lottie_subset(doc)
    assert validation.supported is False
    assert "nonfinite_numeric" in validation.unsupported
    assert "invalid_fps" in validation.unsupported


def test_lottie_validation_rejects_boolean_layer_index():
    doc = {
        "v": "5.12.0",
        "fr": 30,
        "ip": 0,
        "op": 30,
        "w": 640,
        "h": 360,
        "assets": [],
        "layers": [
            {
                "type": "shape",
                "ty": 4,
                "ind": True,
                "nm": "layer",
                "features": [],
                "shapes": [],
            }
        ],
    }
    validation = validate_lottie_subset(doc)
    assert validation.supported is False
    assert "invalid_layer_index" in validation.unsupported


def test_lottie_validation_rejects_duplicate_asset_identity():
    doc = {
        "v": "5.12.0",
        "fr": 30,
        "ip": 0,
        "op": 30,
        "w": 640,
        "h": 360,
        "assets": [{"id": "dup"}, {"id": "dup"}],
        "layers": [],
    }
    validation = validate_lottie_subset(doc)
    assert validation.supported is False
    assert "duplicate_asset_id" in validation.unsupported
