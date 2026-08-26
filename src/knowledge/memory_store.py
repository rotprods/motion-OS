from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence
import json
import sqlite3


MEMORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS graph_memories (
  id TEXT PRIMARY KEY,
  memory_plane TEXT NOT NULL,
  node_id TEXT,
  payload_json TEXT NOT NULL,
  vector_json TEXT,
  semantic_score REAL NOT NULL DEFAULT 0,
  style_score REAL NOT NULL DEFAULT 0,
  motion_score REAL NOT NULL DEFAULT 0,
  composition_score REAL NOT NULL DEFAULT 0,
  brand_score REAL NOT NULL DEFAULT 0,
  historical_qa REAL NOT NULL DEFAULT 0,
  user_approval REAL NOT NULL DEFAULT 0,
  license_ok INTEGER NOT NULL DEFAULT 1,
  asset_type TEXT,
  aspect_ratio TEXT,
  renderer_support_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_graph_memories_plane ON graph_memories(memory_plane);
CREATE INDEX IF NOT EXISTS idx_graph_memories_asset_type ON graph_memories(asset_type);
"""

MEMORY_PLANES = {
    'reference', 'style', 'motion', 'success', 'failure', 'renderer', 'asset', 'user_feedback'
}


def connect_memory_store(path: str | Path = ':memory:') -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(MEMORY_SCHEMA)
    return conn


def upsert_memory(
    conn: sqlite3.Connection,
    *,
    memory_id: str,
    memory_plane: str,
    payload: dict[str, Any],
    node_id: str | None = None,
    vector: Sequence[float] | None = None,
    semantic_score: float = 0,
    style_score: float = 0,
    motion_score: float = 0,
    composition_score: float = 0,
    brand_score: float = 0,
    historical_qa: float = 0,
    user_approval: float = 0,
    license_ok: bool = True,
    asset_type: str | None = None,
    aspect_ratio: str | None = None,
    renderer_support: Sequence[str] = (),
) -> None:
    if memory_plane not in MEMORY_PLANES:
        raise ValueError(f'unknown memory plane: {memory_plane}')
    scores = (semantic_score, style_score, motion_score, composition_score, brand_score, historical_qa, user_approval)
    if any(not 0 <= value <= 1 for value in scores):
        raise ValueError('memory scores must be within [0,1]')
    conn.execute(
        """INSERT INTO graph_memories(
             id,memory_plane,node_id,payload_json,vector_json,semantic_score,style_score,motion_score,
             composition_score,brand_score,historical_qa,user_approval,license_ok,asset_type,aspect_ratio,
             renderer_support_json)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET
             memory_plane=excluded.memory_plane,node_id=excluded.node_id,payload_json=excluded.payload_json,
             vector_json=excluded.vector_json,semantic_score=excluded.semantic_score,style_score=excluded.style_score,
             motion_score=excluded.motion_score,composition_score=excluded.composition_score,brand_score=excluded.brand_score,
             historical_qa=excluded.historical_qa,user_approval=excluded.user_approval,license_ok=excluded.license_ok,
             asset_type=excluded.asset_type,aspect_ratio=excluded.aspect_ratio,renderer_support_json=excluded.renderer_support_json""",
        (
            memory_id, memory_plane, node_id, json.dumps(payload, sort_keys=True),
            json.dumps(list(vector)) if vector is not None else None,
            semantic_score, style_score, motion_score, composition_score, brand_score,
            historical_qa, user_approval, int(license_ok), asset_type, aspect_ratio,
            json.dumps(sorted(set(renderer_support))),
        ),
    )
    conn.commit()


def load_memories(conn: sqlite3.Connection, *, memory_planes: set[str] | None = None) -> list[dict[str, Any]]:
    rows = conn.execute('SELECT * FROM graph_memories').fetchall()
    result = []
    for row in rows:
        if memory_planes and row['memory_plane'] not in memory_planes:
            continue
        result.append({
            'id': row['id'],
            'memory_plane': row['memory_plane'],
            'node_id': row['node_id'],
            'payload': json.loads(row['payload_json']),
            'vector': json.loads(row['vector_json']) if row['vector_json'] else None,
            'semantic_score': row['semantic_score'],
            'style_score': row['style_score'],
            'motion_score': row['motion_score'],
            'composition_score': row['composition_score'],
            'brand_score': row['brand_score'],
            'historical_qa': row['historical_qa'],
            'user_approval': row['user_approval'],
            'license_ok': bool(row['license_ok']),
            'asset_type': row['asset_type'],
            'aspect_ratio': row['aspect_ratio'],
            'renderer_support': json.loads(row['renderer_support_json'] or '[]'),
        })
    return result
