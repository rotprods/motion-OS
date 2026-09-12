from __future__ import annotations

import math

import pytest

from src.semantic_index.clients import HttpResponse, OllamaClient, QdrantClient, SemanticServiceError
from src.semantic_index.core import SemanticConfig
from src.semantic_index.engine import SemanticKnowledgePlane
from tests.test_semantic_index import FakeHttp, FakeOllama, FakeQdrant, _unit


@pytest.mark.parametrize('value', [None, [], [0.0] * 1024, [math.nan] * 1024, [math.inf] * 1024, [True] * 1024, ['1'] * 1024])
def test_search_rejects_missing_or_invalid_native_vectors(value):
    qdrant = FakeQdrant()
    qdrant.query_results = [{'id': 'corrupt', 'score': 0.999, 'vector': {'semantic': value}, 'payload': {'path': 'corrupt.py'}}]
    plane = SemanticKnowledgePlane(SemanticConfig(), ollama=FakeOllama(vectors=[_unit(0)]), qdrant=qdrant)
    with pytest.raises(SemanticServiceError):
        plane.search('native evidence required')


@pytest.mark.parametrize('value', [[0.0] * 1024, [math.nan] * 1024, [math.inf] * 1024, [True] * 1024, ['1'] * 1024])
def test_ollama_rejects_nonsemantic_vectors(value):
    client = OllamaClient(SemanticConfig(), http=FakeHttp([HttpResponse(200, {'embeddings': [value]})]))
    with pytest.raises(SemanticServiceError):
        client.embed(['query'])


@pytest.mark.parametrize('response', [None, {}, [], [{'points': []}], [{'points': []}, {'points': []}, {'points': []}], [{'points': None}, {'points': []}], [[None], []]])
def test_query_batch_rejects_missing_malformed_or_extra_responses(response):
    with pytest.raises(SemanticServiceError):
        QdrantClient._parse_query_batch(response, 2)


def test_empty_successful_batches_remain_valid():
    assert QdrantClient._parse_query_batch([{'points': []}, []], 2) == [[], []]


@pytest.mark.parametrize('result', [None, {}, {'points': None}, {'points': [None]}, 7])
def test_query_rejects_malformed_provider_result(result):
    client = QdrantClient(SemanticConfig(), http=FakeHttp([HttpResponse(200, {'result': result})]))
    with pytest.raises(SemanticServiceError):
        client.query(_unit(0, 20), using='cos20', limit=5)


@pytest.mark.parametrize('distance', ['Dot', 'Euclid', None])
def test_existing_collection_requires_cosine_distance(distance):
    body = {'result': {'config': {'params': {'vectors': {
        'semantic': {'size': 1024, 'distance': distance},
        'cos20': {'size': 20, 'distance': 'Cosine'},
    }}}}}
    client = QdrantClient(SemanticConfig(), http=FakeHttp([HttpResponse(200, body)]))
    with pytest.raises(SemanticServiceError):
        client.ensure_collection()


def test_graphify_does_not_overwrite_graph_after_malformed_batch():
    class MalformedBatchQdrant(FakeQdrant):
        def scroll(self, **kwargs):
            return [{'id': 'existing', 'payload': {'graph_neighbors': [{'id': 'preserve-me'}]}}]

        def query_prefetch_rerank_by_ids_batch(self, *args, **kwargs):
            return QdrantClient._parse_query_batch(None, 1)

        def set_payload_batch(self, updates):
            self.events.append('set_payload_batch')

    qdrant = MalformedBatchQdrant()
    plane = SemanticKnowledgePlane(SemanticConfig(), ollama=FakeOllama(), qdrant=qdrant)
    with pytest.raises(SemanticServiceError):
        plane.graphify()
    assert 'set_payload_batch' not in qdrant.events


@pytest.mark.parametrize('point', [
    {},
    {'id': None, 'score': 0.8, 'payload': {}},
    {'id': True, 'score': 0.8, 'payload': {}},
    {'id': -1, 'score': 0.8, 'payload': {}},
    {'id': ' ', 'score': 0.8, 'payload': {}},
    {'id': 'neighbor', 'score': math.nan, 'payload': {}},
    {'id': 'neighbor', 'score': math.inf, 'payload': {}},
    {'id': 'neighbor', 'score': True, 'payload': {}},
    {'id': 'neighbor', 'score': '0.8', 'payload': {}},
    {'id': 'neighbor', 'score': 0.8, 'payload': None},
    {'id': 'neighbor', 'score': 0.8, 'payload': []},
])
def test_graphify_preserves_existing_neighbors_on_corrupt_point(point):
    client = QdrantClient(SemanticConfig(), http=FakeHttp([HttpResponse(200, {'result': [
        {'points': [{'id': 'valid', 'score': 0.9, 'payload': {'repo': 'rotprods/test'}}]},
        {'points': [point]},
    ]})]))
    client.ensure_collection = lambda: {}
    client.scroll = lambda **kwargs: [
        {'id': 'a', 'payload': {'graph_neighbors': [{'id': 'preserved-a'}]}},
        {'id': 'b', 'payload': {'graph_neighbors': [{'id': 'preserved-b'}]}},
    ]
    writes = []
    client.set_payload_batch = lambda updates: writes.append(updates)
    plane = SemanticKnowledgePlane(SemanticConfig(), ollama=FakeOllama(), qdrant=client)
    with pytest.raises(SemanticServiceError):
        plane.graphify()
    assert writes == []


def test_valid_zero_id_and_zero_score_are_preserved():
    point = {'id': 0, 'score': 0, 'payload': {}}
    assert QdrantClient._parse_query_points({'points': [point]}) == [point]
