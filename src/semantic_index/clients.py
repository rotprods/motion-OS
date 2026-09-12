from __future__ import annotations

import json
import math
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from .core import SemanticConfig


class SemanticServiceError(RuntimeError):
    pass


def validate_semantic_vector(value: object, dims: int) -> list[float]:
    """Reject provider corruption before it can become semantic evidence."""
    if not isinstance(value, list) or len(value) != dims:
        raise SemanticServiceError(f"semantic vector must contain exactly {dims} dimensions")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in value):
        raise SemanticServiceError("semantic vector components must be JSON numbers")
    try:
        vector = [float(v) for v in value]
        norm_squared = sum(v * v for v in vector)
    except (ValueError, OverflowError) as exc:
        raise SemanticServiceError("semantic vector is not representable") from exc
    if not all(math.isfinite(v) for v in vector) or not math.isfinite(norm_squared) or norm_squared <= 0:
        raise SemanticServiceError("semantic vector must have a finite, nonzero norm")
    return vector


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: dict[str, Any]


class JsonHttpClient:
    def __init__(self, base_url: str, *, timeout: float, headers: dict[str, str] | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {"Content-Type": "application/json", **(headers or {})}

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None, *, allow_status: Iterable[int] = ()) -> HttpResponse:
        data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
        req = urllib.request.Request(f"{self.base_url}{path}", method=method, data=data, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read()
                body = json.loads(raw.decode("utf-8")) if raw else {}
                return HttpResponse(status=response.status, body=body)
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                body = json.loads(raw.decode("utf-8")) if raw else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                body = {"raw": raw.decode("utf-8", errors="replace")}
            if exc.code in set(allow_status):
                return HttpResponse(status=exc.code, body=body)
            raise SemanticServiceError(f"{method} {self.base_url}{path} failed with HTTP {exc.code}: {body}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise SemanticServiceError(f"{method} {self.base_url}{path} failed: {exc}") from exc


class OllamaClient:
    def __init__(self, config: SemanticConfig, *, http: JsonHttpClient | None = None):
        self.config = config
        self.http = http or JsonHttpClient(config.ollama_url, timeout=config.timeout_seconds)

    def health(self) -> dict[str, Any]:
        return self.http.request("GET", "/api/tags").body

    def embed(self, inputs: Sequence[str]) -> list[list[float]]:
        response = self.http.request("POST", "/api/embed", {"model": self.config.ollama_model, "input": list(inputs), "truncate": True}).body
        embeddings = response.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(inputs):
            raise SemanticServiceError(f"Ollama returned {len(embeddings) if isinstance(embeddings, list) else 'invalid'} embeddings for {len(inputs)} inputs")
        result: list[list[float]] = []
        for vector in embeddings:
            if not isinstance(vector, list) or len(vector) != self.config.semantic_dims:
                raise SemanticServiceError(f"embedding dimension mismatch: expected {self.config.semantic_dims}, got {len(vector) if isinstance(vector, list) else 'invalid'}")
            result.append(validate_semantic_vector(vector, self.config.semantic_dims))
        return result


class QdrantClient:
    def __init__(self, config: SemanticConfig, *, http: JsonHttpClient | None = None):
        headers = {"api-key": config.qdrant_api_key} if config.qdrant_api_key else None
        self.config = config
        self.http = http or JsonHttpClient(config.qdrant_url, timeout=config.timeout_seconds, headers=headers)

    @property
    def collection_path(self) -> str:
        return f"/collections/{urllib.parse.quote(self.config.qdrant_collection, safe='')}"

    def health(self) -> dict[str, Any]:
        return self.http.request("GET", "/collections").body

    def ensure_collection(self) -> dict[str, Any]:
        current = self.http.request("GET", self.collection_path, allow_status=(404,))
        if current.status == 404:
            created = self.http.request("PUT", self.collection_path, {"vectors": {"semantic": {"size": self.config.semantic_dims, "distance": "Cosine"}, "cos20": {"size": self.config.cos_dims, "distance": "Cosine"}}}).body
            self._ensure_payload_indexes()
            return {"created": True, "response": created}
        self._validate_collection_schema(current.body)
        self._ensure_payload_indexes()
        return {"created": False, "response": current.body}

    def _validate_collection_schema(self, body: dict[str, Any]) -> None:
        try:
            vectors = body["result"]["config"]["params"]["vectors"]
        except (KeyError, TypeError) as exc:
            raise SemanticServiceError("Qdrant collection metadata missing named-vector schema") from exc
        expected = {"semantic": self.config.semantic_dims, "cos20": self.config.cos_dims}
        for name, dims in expected.items():
            spec = vectors.get(name) if isinstance(vectors, dict) else None
            size = spec.get("size") if isinstance(spec, dict) else None
            if int(size or -1) != dims:
                raise SemanticServiceError(f"collection {self.config.qdrant_collection!r} vector {name!r} has size {size}; expected {dims}. Use a versioned collection name instead of mutating incompatible data.")
            if spec.get("distance") != "Cosine":
                raise SemanticServiceError(f"collection vector {name!r} must use Cosine distance; use a compatible versioned collection")

    def _ensure_payload_indexes(self) -> None:
        for field in ("repo", "path", "index_run", "commit"):
            response = self.http.request("PUT", f"{self.collection_path}/index?wait=true", {"field_name": field, "field_schema": "keyword"}, allow_status=(400, 409))
            if response.status not in (200, 201, 400, 409):
                raise SemanticServiceError(f"failed to ensure payload index for {field}")

    def upsert(self, points: Sequence[dict[str, Any]]) -> dict[str, Any]:
        if not points:
            return {"status": "noop"}
        return self.http.request("PUT", f"{self.collection_path}/points?wait=true", {"points": list(points)}).body

    def delete_stale(self, repo_id: str, index_run: str) -> dict[str, Any]:
        return self.http.request("POST", f"{self.collection_path}/points/delete?wait=true", {"filter": {"must": [{"key": "repo", "match": {"value": repo_id}}], "must_not": [{"key": "index_run", "match": {"value": index_run}}]}}).body

    @staticmethod
    def _repo_filter(repo_ids: Sequence[str] | None) -> dict[str, Any] | None:
        if not repo_ids:
            return None
        return {"should": [{"key": "repo", "match": {"value": repo_id}} for repo_id in repo_ids]}

    @staticmethod
    def _parse_query_points(result: object) -> list[dict[str, Any]]:
        points = result.get("points") if isinstance(result, dict) else result
        if not isinstance(points, list) or any(not isinstance(point, dict) for point in points):
            raise SemanticServiceError("Qdrant query response must contain a list of point objects")
        for point in points:
            point_id = point.get("id")
            if not ((isinstance(point_id, str) and bool(point_id.strip())) or (type(point_id) is int and point_id >= 0)):
                raise SemanticServiceError("Qdrant point identity must be a nonempty string or unsigned integer")
            score = point.get("score")
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                raise SemanticServiceError("Qdrant point score must be a finite JSON number")
            try:
                finite_score = math.isfinite(score)
            except OverflowError:
                finite_score = False
            if not finite_score:
                raise SemanticServiceError("Qdrant point score must be a finite JSON number")
            if not isinstance(point.get("payload"), dict):
                raise SemanticServiceError("Qdrant point payload must be an object")
        return points

    @staticmethod
    def _parse_query_batch(result: object, expected: int) -> list[list[dict[str, Any]]]:
        if not isinstance(result, list) or len(result) != expected:
            raise SemanticServiceError(f"Qdrant batch response must contain exactly {expected} query results")
        return [QdrantClient._parse_query_points(item) for item in result]

    def query(self, vector: Sequence[float], *, using: str, limit: int, repo_ids: Sequence[str] | None = None, with_vectors: Sequence[str] | bool = False) -> list[dict[str, Any]]:
        body: dict[str, Any] = {"query": [float(v) for v in vector], "using": using, "limit": int(limit), "with_payload": True, "with_vector": list(with_vectors) if isinstance(with_vectors, (list, tuple)) else bool(with_vectors)}
        repo_filter = self._repo_filter(repo_ids)
        if repo_filter:
            body["filter"] = repo_filter
        response = self.http.request("POST", f"{self.collection_path}/points/query", body).body
        return self._parse_query_points(response.get("result"))

    def query_batch(self, vectors: Sequence[Sequence[float]], *, using: str, limit: int, repo_ids: Sequence[str] | None = None, with_vectors: Sequence[str] | bool = False) -> list[list[dict[str, Any]]]:
        repo_filter = self._repo_filter(repo_ids)
        searches: list[dict[str, Any]] = []
        for vector in vectors:
            body: dict[str, Any] = {"query": [float(v) for v in vector], "using": using, "limit": int(limit), "with_payload": True, "with_vector": list(with_vectors) if isinstance(with_vectors, (list, tuple)) else bool(with_vectors)}
            if repo_filter:
                body["filter"] = repo_filter
            searches.append(body)
        if not searches:
            return []
        response = self.http.request("POST", f"{self.collection_path}/points/query/batch", {"searches": searches}).body
        return self._parse_query_batch(response.get("result", []), len(searches))

    def query_prefetch_rerank_by_ids_batch(
        self,
        point_ids: Sequence[str | int],
        *,
        candidate_limit: int,
        limit: int,
        repo_ids: Sequence[str] | None = None,
        score_threshold: float | None = None,
    ) -> list[list[dict[str, Any]]]:
        """Route by stored cos20 vectors, then rerank the candidate set by stored semantic vectors in Qdrant."""
        if candidate_limit < limit:
            raise ValueError("candidate_limit must be >= limit")
        repo_filter = self._repo_filter(repo_ids)
        searches: list[dict[str, Any]] = []
        for point_id in point_ids:
            prefetch: dict[str, Any] = {
                "query": point_id,
                "using": "cos20",
                "limit": int(candidate_limit),
            }
            if repo_filter:
                prefetch["filter"] = repo_filter
            body: dict[str, Any] = {
                "prefetch": prefetch,
                "query": point_id,
                "using": "semantic",
                "limit": int(limit),
                "with_payload": True,
                "with_vector": False,
            }
            if repo_filter:
                body["filter"] = repo_filter
            if score_threshold is not None:
                body["score_threshold"] = float(score_threshold)
            searches.append(body)
        if not searches:
            return []
        response = self.http.request("POST", f"{self.collection_path}/points/query/batch", {"searches": searches}).body
        return self._parse_query_batch(response.get("result", []), len(searches))

    def scroll(self, *, repo_ids: Sequence[str] | None = None, with_vectors: Sequence[str] | bool = False, page_size: int = 128) -> list[dict[str, Any]]:
        points: list[dict[str, Any]] = []
        offset: Any = None
        while True:
            body: dict[str, Any] = {"limit": page_size, "with_payload": True, "with_vector": list(with_vectors) if isinstance(with_vectors, (list, tuple)) else bool(with_vectors)}
            if offset is not None:
                body["offset"] = offset
            repo_filter = self._repo_filter(repo_ids)
            if repo_filter:
                body["filter"] = repo_filter
            response = self.http.request("POST", f"{self.collection_path}/points/scroll", body).body
            result = response.get("result", {})
            batch = result.get("points", []) if isinstance(result, dict) else []
            if not isinstance(batch, list):
                break
            points.extend(batch)
            offset = result.get("next_page_offset") if isinstance(result, dict) else None
            if offset is None or not batch:
                break
        return points

    def set_payload(self, point_id: str | int, payload: dict[str, Any]) -> dict[str, Any]:
        return self.http.request("POST", f"{self.collection_path}/points/payload?wait=true", {"payload": payload, "points": [point_id]}).body

    def set_payload_batch(self, updates: Sequence[tuple[str | int, dict[str, Any]]]) -> dict[str, Any]:
        if not updates:
            return {"status": "noop"}
        operations = [{"set_payload": {"payload": payload, "points": [point_id]}} for point_id, payload in updates]
        return self.http.request("POST", f"{self.collection_path}/points/batch?wait=true", {"operations": operations}).body
