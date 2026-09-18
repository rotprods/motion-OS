from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import hashlib
import json

SUPPORTED_LAYER_TYPES = frozenset({"shape", "text", "image", "precomp", "null"})
SUPPORTED_FEATURES = frozenset({
    "transform", "opacity", "position", "scale", "rotation",
    "shape_path", "fill", "stroke", "trim_path", "mask", "marker",
})
LOTTIE_TYPE_CODE = {"precomp": 0, "image": 2, "null": 3, "shape": 4, "text": 5}
TYPE_FROM_CODE = {value: key for key, value in LOTTIE_TYPE_CODE.items()}


@dataclass(frozen=True)
class LottieValidation:
    supported: bool
    unsupported: tuple[str, ...]
    warnings: tuple[str, ...]


def _stable_json_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _default_transform(data: dict[str, Any]) -> dict[str, Any]:
    transform = data.get("transform") or {}
    return {
        "o": {"a": 0, "k": float(transform.get("opacity", 100))},
        "r": {"a": 0, "k": float(transform.get("rotation", 0))},
        "p": {"a": 0, "k": list(transform.get("position", [0, 0, 0]))},
        "a": {"a": 0, "k": list(transform.get("anchor", [0, 0, 0]))},
        "s": {"a": 0, "k": list(transform.get("scale", [100, 100, 100]))},
    }


def _layer_type(layer: dict[str, Any]) -> str | None:
    declared = layer.get("type")
    if declared is not None:
        return str(declared)
    return TYPE_FROM_CODE.get(layer.get("ty"))


def _contains_expression(value: Any) -> bool:
    if isinstance(value, dict):
        if isinstance(value.get("x"), str) and value.get("x", "").strip():
            return True
        return any(_contains_expression(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_expression(child) for child in value)
    return False


def validate_lottie_subset(doc: dict[str, Any]) -> LottieValidation:
    """Validate MOTION.OS' deliberately small, player-oriented Lottie subset.

    This is a compiler/subset validator. It does not claim that a physical player
    has rendered the document.
    """
    unsupported: list[str] = []
    warnings: list[str] = []
    try:
        fps = float(doc.get("fr", 0))
        in_frame = float(doc.get("ip", 0))
        out_frame = float(doc.get("op", 0))
        width = int(doc.get("w", 0))
        height = int(doc.get("h", 0))
    except (TypeError, ValueError):
        fps = in_frame = out_frame = 0
        width = height = 0

    if fps <= 0:
        unsupported.append("invalid_fps")
    if out_frame <= in_frame:
        unsupported.append("invalid_frame_range")
    if width <= 0 or height <= 0:
        unsupported.append("invalid_canvas")

    layers = doc.get("layers", [])
    if not isinstance(layers, list):
        unsupported.append("layers_not_array")
        layers = []
    assets = doc.get("assets", [])
    if not isinstance(assets, list):
        unsupported.append("assets_not_array")
        assets = []
    asset_ids = {
        asset.get("id") for asset in assets
        if isinstance(asset, dict) and asset.get("id")
    }

    indices: list[int] = []
    names: list[str] = []
    for layer in layers:
        if not isinstance(layer, dict):
            unsupported.append("layer_not_object")
            continue
        typ = _layer_type(layer)
        if typ not in SUPPORTED_LAYER_TYPES:
            unsupported.append(f"layer_type:{typ}")
            continue
        if layer.get("ty") != LOTTIE_TYPE_CODE[typ]:
            unsupported.append(f"layer_type_code_mismatch:{layer.get('nm', '<unnamed>')}")

        index = layer.get("ind")
        name = layer.get("nm")
        if not isinstance(index, int) or index <= 0:
            unsupported.append("invalid_layer_index")
        else:
            indices.append(index)
        if not isinstance(name, str) or not name.strip():
            unsupported.append("missing_stable_layer_id")
        else:
            names.append(name)

        for feature in layer.get("features", []):
            if feature not in SUPPORTED_FEATURES:
                unsupported.append(f"feature:{feature}")
        if layer.get("expressions") or _contains_expression(layer):
            unsupported.append("expressions")
        if layer.get("text") and layer.get("rasterized_text"):
            warnings.append("rasterized_text_breaks_text_integrity")

        if typ in {"image", "precomp"}:
            ref_id = layer.get("refId")
            if not ref_id:
                unsupported.append(f"missing_ref_id:{name or index}")
            elif ref_id not in asset_ids:
                unsupported.append(f"unresolved_asset_ref:{ref_id}")
        if typ == "text" and "t" not in layer:
            unsupported.append(f"missing_text_document:{name or index}")
        if typ == "shape" and not isinstance(layer.get("shapes", []), list):
            unsupported.append(f"invalid_shapes:{name or index}")

    if len(indices) != len(set(indices)):
        unsupported.append("duplicate_layer_index")
    if len(names) != len(set(names)):
        unsupported.append("duplicate_stable_layer_id")

    return LottieValidation(
        not unsupported,
        tuple(sorted(set(unsupported))),
        tuple(sorted(set(warnings))),
    )


def _compile_layer(
    element: dict[str, Any],
    *,
    index: int,
    in_frame: int,
    out_frame: int,
) -> dict[str, Any]:
    element_id = str(element.get("id", "")).strip()
    if not element_id:
        raise ValueError("Lottie element id must be non-empty")
    typ = str(element.get("type", "shape"))
    if typ not in SUPPORTED_LAYER_TYPES:
        raise ValueError(f"Unsupported Lottie layer type: {typ}")

    features = list(element.get("features", []))
    unsupported_features = sorted(set(features) - SUPPORTED_FEATURES)
    if unsupported_features:
        raise ValueError("Unsupported Lottie features: " + ",".join(unsupported_features))

    data = dict(element.get("data") or {})
    layer: dict[str, Any] = {
        "ddd": 0,
        "ind": index,
        "ty": LOTTIE_TYPE_CODE[typ],
        "nm": element_id,
        "sr": 1,
        "ks": _default_transform(data),
        "ao": 0,
        "ip": int(element.get("in_frame", in_frame)),
        "op": int(element.get("out_frame", out_frame)),
        "st": int(element.get("start_frame", in_frame)),
        "bm": 0,
        "type": typ,
        "features": features,
        "motion_os": {
            "stable_id": element_id,
            "continuity_id": element.get("continuity_id", element_id),
        },
    }
    if layer["op"] <= layer["ip"]:
        raise ValueError(f"Invalid Lottie layer frame range: {element_id}")

    if typ == "shape":
        layer["shapes"] = list(data.get("shapes", []))
    elif typ == "text":
        text_document = data.get("lottie_text")
        if not isinstance(text_document, dict):
            raise ValueError(f"Text layer requires data.lottie_text document: {element_id}")
        layer["t"] = text_document
    elif typ in {"image", "precomp"}:
        ref_id = str(data.get("ref_id", "")).strip()
        if not ref_id:
            raise ValueError(f"{typ} layer requires data.ref_id: {element_id}")
        layer["refId"] = ref_id
    return layer


def compile_vector_subgraph_to_lottie(
    elements: list[dict[str, Any]],
    *,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    in_frame: int = 0,
    out_frame: int = 300,
    markers: list[dict[str, Any]] | None = None,
    assets: list[dict[str, Any]] | None = None,
    fonts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if width <= 0 or height <= 0:
        raise ValueError("Lottie canvas dimensions must be positive")
    if fps <= 0:
        raise ValueError("Lottie fps must be positive")
    if out_frame <= in_frame:
        raise ValueError("Lottie out_frame must be greater than in_frame")

    ids = [str(element.get("id", "")).strip() for element in elements]
    if any(not element_id for element_id in ids):
        raise ValueError("Every Lottie element requires a stable non-empty id")
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate Lottie stable element id")

    layers = [
        _compile_layer(element, index=index + 1, in_frame=in_frame, out_frame=out_frame)
        for index, element in enumerate(elements)
    ]
    doc: dict[str, Any] = {
        "v": "5.12.0",
        "fr": fps,
        "ip": in_frame,
        "op": out_frame,
        "w": width,
        "h": height,
        "nm": "MOTION.OS vector subgraph",
        "ddd": 0,
        "assets": list(assets or []),
        "layers": layers,
        "markers": list(markers or []),
    }
    if fonts is not None:
        doc["fonts"] = fonts

    result = validate_lottie_subset(doc)
    if not result.supported:
        raise ValueError("Unsupported Lottie subset: " + ",".join(result.unsupported))
    return doc


def player_roundtrip_contract(doc: dict[str, Any], *, player: str = "lottie-web") -> dict[str, Any]:
    """Define the evidence a physical Lottie player run must bind before release."""
    validation = validate_lottie_subset(doc)
    if not validation.supported:
        raise ValueError("Cannot create player contract for unsupported Lottie document")
    if player not in {"lottie-web", "dotlottie-web"}:
        raise ValueError("Unsupported Lottie player contract")
    return {
        "player": player,
        "authority": "compiler_ready",
        "document_sha256": _stable_json_hash(doc),
        "fps": doc["fr"],
        "in_frame": doc["ip"],
        "out_frame": doc["op"],
        "expected_frame_count": int(doc["op"] - doc["ip"]),
        "stable_layer_ids": [layer["nm"] for layer in doc["layers"]],
        "requires_physical_player_execution": True,
        "requires_frame_evidence": True,
        "text_integrity": "strict",
    }


def embed_contract(*, asset_id: str, lottie_path: str, target_renderer: str) -> dict[str, Any]:
    if target_renderer not in {"remotion", "hyperframes"}:
        raise ValueError("target_renderer must be remotion or hyperframes")
    if not asset_id.strip() or not lottie_path.strip():
        raise ValueError("asset_id and lottie_path must be non-empty")
    return {
        "asset_id": asset_id,
        "kind": "lottie",
        "path": lottie_path,
        "target_renderer": target_renderer,
        "stable_ids_required": True,
        "text_integrity": "strict",
        "physical_player_authority_required_for_release": True,
    }
