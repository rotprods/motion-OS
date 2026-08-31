import hashlib
import json

import pytest

from scripts.build_lottie_runtime_fixture import build_fixture
from scripts.verify_lottie_player import canonical_json_hash
from src.compilers.lottie import (
    compile_vector_subgraph_to_lottie,
    player_roundtrip_contract,
    validate_lottie_subset,
)


def _shape():
    return {
        'id': 'ring',
        'type': 'shape',
        'features': ['transform', 'fill', 'trim_path'],
        'data': {
            'transform': {'position': [540, 960, 0], 'scale': [100, 100, 100]},
            'shapes': [],
        },
    }


def test_compiler_emits_player_oriented_lottie_layer_contract():
    doc = compile_vector_subgraph_to_lottie([_shape()], fps=30, in_frame=0, out_frame=60)
    layer = doc['layers'][0]

    assert doc['v'] == '5.12.0'
    assert doc['fr'] == 30
    assert doc['assets'] == []
    assert layer['ty'] == 4
    assert layer['nm'] == 'ring'
    assert layer['motion_os']['stable_id'] == 'ring'
    assert layer['ks']['p']['k'] == [540, 960, 0]
    assert layer['shapes'] == []
    assert validate_lottie_subset(doc).supported is True


def test_duplicate_stable_ids_fail_before_document_creation():
    with pytest.raises(ValueError, match='Duplicate Lottie stable element id'):
        compile_vector_subgraph_to_lottie([_shape(), _shape()])


def test_image_and_precomp_refs_must_resolve_to_declared_assets():
    image = {
        'id': 'photo',
        'type': 'image',
        'features': ['transform'],
        'data': {'ref_id': 'image_01'},
    }
    with pytest.raises(ValueError, match='unresolved_asset_ref:image_01'):
        compile_vector_subgraph_to_lottie([image])

    doc = compile_vector_subgraph_to_lottie(
        [image],
        assets=[{'id': 'image_01', 'w': 100, 'h': 100, 'p': 'photo.png', 'u': ''}],
    )
    assert doc['layers'][0]['refId'] == 'image_01'
    assert validate_lottie_subset(doc).supported is True


def test_text_layer_requires_explicit_lottie_text_document():
    with pytest.raises(ValueError, match='requires data.lottie_text'):
        compile_vector_subgraph_to_lottie([
            {'id': 'headline', 'type': 'text', 'features': ['transform'], 'data': {}}
        ])


def test_validator_rejects_expression_and_timing_corruption():
    doc = compile_vector_subgraph_to_lottie([_shape()], out_frame=30)
    broken = dict(doc)
    layer = dict(doc['layers'][0])
    layer['ks'] = dict(layer['ks'])
    layer['ks']['r'] = {'a': 0, 'k': 0, 'x': 'time * 20'}
    broken['layers'] = [layer]
    broken['op'] = 0

    result = validate_lottie_subset(broken)
    assert result.supported is False
    assert 'expressions' in result.unsupported
    assert 'invalid_frame_range' in result.unsupported


def test_player_roundtrip_contract_never_self_promotes_without_physical_evidence():
    doc = compile_vector_subgraph_to_lottie([_shape()], fps=30, out_frame=60)
    contract = player_roundtrip_contract(doc, player='lottie-web')
    again = player_roundtrip_contract(doc, player='lottie-web')

    assert contract == again
    assert contract['authority'] == 'compiler_ready'
    assert contract['expected_frame_count'] == 60
    assert contract['stable_layer_ids'] == ['ring']
    assert contract['requires_physical_player_execution'] is True
    assert contract['requires_frame_evidence'] is True
    assert len(contract['document_sha256']) == 64


def test_invalid_player_contract_fails_closed():
    doc = compile_vector_subgraph_to_lottie([_shape()])
    with pytest.raises(ValueError, match='Unsupported Lottie player contract'):
        player_roundtrip_contract(doc, player='unknown-player')


def test_runtime_fixture_binds_compiler_document_and_contains_real_motion(tmp_path):
    evidence = build_fixture(tmp_path)
    animation_path = tmp_path / 'animation.json'
    contract_path = tmp_path / 'player_contract.json'
    html_path = tmp_path / 'index.html'

    document = json.loads(animation_path.read_text(encoding='utf-8'))
    contract = json.loads(contract_path.read_text(encoding='utf-8'))
    html = html_path.read_text(encoding='utf-8')

    assert canonical_json_hash(document) == contract['document_sha256'] == evidence['document_sha256']
    assert hashlib.sha256(animation_path.read_bytes()).hexdigest() == evidence['animation_file_sha256']
    assert evidence['expected_frame_count'] == 60
    assert evidence['stable_layer_ids'] == ['runtime_ring']
    assert evidence['authority'] == 'compiler_ready'

    trim_path = document['layers'][0]['shapes'][0]['it'][2]
    assert trim_path['ty'] == 'tm'
    assert trim_path['e']['a'] == 1
    assert trim_path['e']['k'][0]['s'] == [5]
    assert trim_path['e']['k'][-1]['s'] == [100]

    assert "renderer: 'svg'" in html
    assert "autoplay: false" in html
    assert "loop: false" in html
    assert "DOMLoaded" in html
    assert "goToAndStop(requestedFrame, true)" in html
