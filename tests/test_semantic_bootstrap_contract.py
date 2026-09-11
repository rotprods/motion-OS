from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts" / "bootstrap_semantic_plane.sh"


def test_bootstrap_has_pinned_docker_ollama_fallback() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert "ollama/ollama:0.33.2" in text
    assert "motion-semantic-ollama" in text
    assert "127.0.0.1:11434:11434" in text
    assert "motion_ollama_models:/root/.ollama" not in text  # volume name remains configurable
    assert '${OLLAMA_VOLUME}:/root/.ollama' in text


def test_bootstrap_uses_http_pull_for_host_and_docker_modes() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert '"${OLLAMA_URL}/api/pull"' in text
    assert '"stream": False' in text
    assert "Host Ollama CLI not found; starting pinned Docker Ollama" in text


def test_bootstrap_fails_closed_for_nonlocal_docker_fallback() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert 'Refusing to start a local Docker Ollama because OLLAMA_URL points elsewhere' in text
    assert 'http://127.0.0.1:11434' in text
    assert 'http://localhost:11434' in text
