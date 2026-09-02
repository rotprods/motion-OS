from __future__ import annotations

import fnmatch
import hashlib
import json
import math
import os
import re
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

COS_LEVELS = (
    "L0 Visual Graph",
    "L1 Execution Graph",
    "L2 State Machine",
    "L3 Dependency Graph",
    "L4 Call Graph",
    "L5 Control Flow Graph",
    "L6 DataFlow Graph",
    "L7 Compute Graph",
    "L8 Knowledge Graph",
    "L9 Semantic Graph",
    "L10 Embedding Graph",
    "L11 GraphRAG",
    "L12 Memory Graph",
    "L13 Agent Graph",
    "L14 Tool Graph",
    "L15 Workflow Graph",
    "L16 Network Graph",
    "L17 Social Graph",
    "L18 Biological Graph",
    "L19 Molecular Graph",
)

DEFAULT_EXCLUDED_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "node_modules",
        "vendor",
        "dist",
        "build",
        ".next",
        ".nuxt",
        ".cache",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "coverage",
        ".coverage",
        ".qdrant",
    }
)

BINARY_SUFFIXES = frozenset(
    {
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".svgz",
        ".mp3", ".wav", ".aac", ".flac", ".mp4", ".mov", ".mkv", ".avi", ".webm",
        ".pdf", ".zip", ".gz", ".bz2", ".xz", ".7z", ".tar", ".rar",
        ".woff", ".woff2", ".ttf", ".otf", ".eot",
        ".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe", ".bin", ".db", ".sqlite",
    }
)

SENSITIVE_NAMES = frozenset(
    {
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        "credentials.json",
        "service-account.json",
        "service_account.json",
        "id_rsa",
        "id_ed25519",
    }
)

_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----.*?-----END(?: [A-Z0-9]+)? PRIVATE KEY-----", re.S),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
)

_TEXT_BOUNDARY = re.compile(r"^\s*(?:$|#{1,6}\s|[-=*]{3,}\s*$|(?:class|def|async def|function|export|interface|type)\s+)")

LANGUAGE_BY_SUFFIX = {
    ".py": "python",
    ".rs": "rust",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "jsx",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".md": "markdown",
    ".mdx": "mdx",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sh": "shell",
    ".zsh": "shell",
    ".sql": "sql",
    ".mmd": "mermaid",
    ".graphql": "graphql",
    ".gql": "graphql",
    ".xml": "xml",
    ".txt": "text",
}


def l2_normalize(vector: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(float(v) * float(v) for v in vector))
    if norm == 0.0:
        return [0.0 for _ in vector]
    return [float(v) / norm for v in vector]


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError(f"vector length mismatch: {len(a)} != {len(b)}")
    aa = l2_normalize(a)
    bb = l2_normalize(b)
    return sum(x * y for x, y in zip(aa, bb))


@dataclass(frozen=True)
class SemanticConfig:
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "bge-m3"
    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_collection: str = "ave_motion_semantic_v1"
    qdrant_api_key: str | None = None
    semantic_dims: int = 1024
    cos_dims: int = 20
    batch_size: int = 16
    timeout_seconds: float = 120.0
    route_multiplier: int = 32

    @classmethod
    def from_env(cls) -> "SemanticConfig":
        return cls(
            ollama_url=os.getenv("OLLAMA_URL", cls.ollama_url).rstrip("/"),
            ollama_model=os.getenv("OLLAMA_EMBED_MODEL", cls.ollama_model),
            qdrant_url=os.getenv("QDRANT_URL", cls.qdrant_url).rstrip("/"),
            qdrant_collection=os.getenv("QDRANT_COLLECTION", cls.qdrant_collection),
            qdrant_api_key=os.getenv("QDRANT_API_KEY") or None,
            semantic_dims=int(os.getenv("SEMANTIC_DIMS", str(cls.semantic_dims))),
            cos_dims=int(os.getenv("COS_ROUTE_DIMS", str(cls.cos_dims))),
            batch_size=max(1, int(os.getenv("SEMANTIC_BATCH_SIZE", str(cls.batch_size)))),
            timeout_seconds=float(os.getenv("SEMANTIC_HTTP_TIMEOUT", str(cls.timeout_seconds))),
            route_multiplier=max(2, int(os.getenv("COS_ROUTE_MULTIPLIER", str(cls.route_multiplier)))),
        )


@dataclass(frozen=True)
class RepoManifest:
    schema_version: int = 1
    repo_id: str | None = None
    include: tuple[str, ...] = ("*", "**/*")
    exclude: tuple[str, ...] = ()
    max_file_bytes: int = 1_572_864
    target_chars: int = 1_600
    max_chars: int = 2_200
    overlap_chars: int = 240
    store_text: bool = True

    @classmethod
    def load(cls, root: Path) -> "RepoManifest":
        path = root / ".semantic-index.json"
        if not path.exists():
            return cls(repo_id=discover_repo_id(root))
        raw = json.loads(path.read_text(encoding="utf-8"))
        chunk = raw.get("chunk", {})
        return cls(
            schema_version=int(raw.get("schema_version", 1)),
            repo_id=str(raw.get("repo_id") or discover_repo_id(root)),
            include=tuple(raw.get("include") or ("*", "**/*")),
            exclude=tuple(raw.get("exclude") or ()),
            max_file_bytes=int(raw.get("max_file_bytes", cls.max_file_bytes)),
            target_chars=int(chunk.get("target_chars", cls.target_chars)),
            max_chars=int(chunk.get("max_chars", cls.max_chars)),
            overlap_chars=int(chunk.get("overlap_chars", cls.overlap_chars)),
            store_text=bool(raw.get("store_text", True)),
        )


@dataclass(frozen=True)
class Chunk:
    repo_id: str
    commit: str
    path: str
    language: str
    start_line: int
    end_line: int
    text: str
    source_sha256: str
    chunk_sha256: str
    point_id: str

    def embedding_text(self) -> str:
        return (
            f"repository: {self.repo_id}\n"
            f"path: {self.path}\n"
            f"language: {self.language}\n"
            f"lines: {self.start_line}-{self.end_line}\n\n"
            f"{self.text}"
        )


@dataclass(frozen=True)
class IndexedChunk:
    chunk: Chunk
    semantic: tuple[float, ...]
    cos20: tuple[float, ...]


@dataclass(frozen=True)
class SearchHit:
    point_id: str
    semantic_score: float
    route_score: float
    payload: dict


class DeterministicJLProjector:
    """Dense deterministic Rademacher JL projection for coarse candidate routing."""

    def __init__(self, output_dims: int = 20, seed: str = "motion-cos20-jl-v2"):
        if output_dims < 2:
            raise ValueError("output_dims must be >= 2")
        self.output_dims = output_dims
        self.seed = seed
        self._sign_cache: dict[int, list[tuple[float, ...]]] = {}

    def _signs(self, input_dims: int) -> list[tuple[float, ...]]:
        cached = self._sign_cache.get(input_dims)
        if cached is not None:
            return cached
        matrix: list[tuple[float, ...]] = []
        for source_index in range(input_dims):
            digest_size = max(8, (self.output_dims + 7) // 8)
            digest = hashlib.blake2b(
                f"{self.seed}:{source_index}".encode("utf-8"), digest_size=digest_size
            ).digest()
            bits = int.from_bytes(digest, "big")
            matrix.append(
                tuple(1.0 if ((bits >> dim) & 1) else -1.0 for dim in range(self.output_dims))
            )
        self._sign_cache[input_dims] = matrix
        return matrix

    def project(self, vector: Sequence[float]) -> list[float]:
        signs = self._signs(len(vector))
        out = [0.0] * self.output_dims
        scale = 1.0 / math.sqrt(self.output_dims)
        for source_index, raw in enumerate(vector):
            value = float(raw) * scale
            row = signs[source_index]
            for dim in range(self.output_dims):
                out[dim] += value * row[dim]
        return l2_normalize(out)


SparseJLProjector = DeterministicJLProjector


def discover_repo_id(root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        remote = completed.stdout.strip().rstrip("/")
        if remote.endswith(".git"):
            remote = remote[:-4]
        if remote.startswith("git@github.com:"):
            remote = remote.split(":", 1)[1]
        elif "github.com/" in remote:
            remote = remote.split("github.com/", 1)[1]
        if "/" in remote:
            return remote
    except (OSError, subprocess.SubprocessError):
        pass
    return root.resolve().name


def discover_commit(root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return completed.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _is_sensitive_path(path: Path) -> bool:
    lower = path.name.lower()
    if lower in SENSITIVE_NAMES:
        return True
    if lower.endswith((".pem", ".key", ".p12", ".pfx")):
        return True
    return False


def _matches_manifest(path: str, manifest: RepoManifest) -> bool:
    normalized = path.replace(os.sep, "/")
    if any(fnmatch.fnmatch(normalized, pattern) for pattern in manifest.exclude):
        return False
    if not manifest.include:
        return True
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in manifest.include)


def _redact_secrets(text: str) -> str:
    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted


def iter_text_files(root: Path, manifest: RepoManifest) -> Iterator[Path]:
    root = root.resolve()
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in DEFAULT_EXCLUDED_DIRS]
        current_path = Path(current)
        for name in files:
            path = current_path / name
            rel = path.relative_to(root)
            if path.is_symlink() or _is_sensitive_path(path):
                continue
            if path.suffix.lower() in BINARY_SUFFIXES:
                continue
            if not _matches_manifest(rel.as_posix(), manifest):
                continue
            try:
                if path.stat().st_size > manifest.max_file_bytes:
                    continue
                prefix = path.read_bytes()[:8192]
            except OSError:
                continue
            if b"\x00" in prefix:
                continue
            yield path


def infer_language(path: Path) -> str:
    if path.name in {"Dockerfile", "Containerfile"}:
        return "dockerfile"
    if path.name == "Makefile":
        return "make"
    return LANGUAGE_BY_SUFFIX.get(path.suffix.lower(), "text")


def _line_char_offsets(lines: list[str]) -> list[int]:
    offsets = [0]
    total = 0
    for line in lines:
        total += len(line)
        offsets.append(total)
    return offsets


def _choose_end(lines: list[str], offsets: list[int], start: int, target: int, max_chars: int) -> int:
    n = len(lines)
    best_boundary: int | None = None
    end = start + 1
    while end <= n:
        chars = offsets[end] - offsets[start]
        if chars >= target and _TEXT_BOUNDARY.match(lines[end - 1]):
            best_boundary = end
            break
        if chars >= max_chars:
            break
        end += 1
    if best_boundary is not None:
        return best_boundary
    end = min(end, n)
    while end > start + 1 and offsets[end] - offsets[start] > max_chars:
        end -= 1
    return max(start + 1, end)


def _overlap_start(lines: list[str], offsets: list[int], start: int, end: int, overlap_chars: int) -> int:
    if overlap_chars <= 0:
        return end
    cursor = end
    while cursor > start + 1 and offsets[end] - offsets[cursor - 1] <= overlap_chars:
        cursor -= 1
    return max(start + 1, cursor)


def chunk_text(
    *,
    repo_id: str,
    commit: str,
    path: str,
    language: str,
    text: str,
    target_chars: int,
    max_chars: int,
    overlap_chars: int,
) -> list[Chunk]:
    if max_chars < target_chars:
        raise ValueError("max_chars must be >= target_chars")
    if overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be < max_chars")

    text = _redact_secrets(text.replace("\r\n", "\n").replace("\r", "\n"))
    source_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    lines = text.splitlines(keepends=True)
    if not lines:
        return []
    offsets = _line_char_offsets(lines)
    chunks: list[Chunk] = []
    start = 0
    while start < len(lines):
        end = _choose_end(lines, offsets, start, target_chars, max_chars)
        raw = "".join(lines[start:end])
        clean = raw.strip()
        if clean:
            chunk_sha = hashlib.sha256(clean.encode("utf-8")).hexdigest()
            stable_key = f"{repo_id}\x1f{path}\x1f{start + 1}\x1f{end}\x1f{chunk_sha}"
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, stable_key))
            chunks.append(
                Chunk(
                    repo_id=repo_id,
                    commit=commit,
                    path=path,
                    language=language,
                    start_line=start + 1,
                    end_line=end,
                    text=clean,
                    source_sha256=source_sha,
                    chunk_sha256=chunk_sha,
                    point_id=point_id,
                )
            )
        next_start = _overlap_start(lines, offsets, start, end, overlap_chars)
        if next_start <= start:
            next_start = end
        start = next_start
    return chunks


def chunk_repository(root: Path, manifest: RepoManifest | None = None) -> list[Chunk]:
    root = root.resolve()
    manifest = manifest or RepoManifest.load(root)
    repo_id = manifest.repo_id or discover_repo_id(root)
    commit = discover_commit(root)
    chunks: list[Chunk] = []
    for file_path in iter_text_files(root, manifest):
        rel = file_path.relative_to(root).as_posix()
        try:
            text = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        chunks.extend(
            chunk_text(
                repo_id=repo_id,
                commit=commit,
                path=rel,
                language=infer_language(file_path),
                text=text,
                target_chars=manifest.target_chars,
                max_chars=manifest.max_chars,
                overlap_chars=manifest.overlap_chars,
            )
        )
    return chunks


def batched(items: Sequence[Chunk], size: int) -> Iterable[Sequence[Chunk]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]
