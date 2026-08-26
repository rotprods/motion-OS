from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from pathlib import Path
from typing import Any, Iterable, Sequence
import json
import sqlite3


SCHEMA = """
CREATE TABLE IF NOT EXISTS style_signatures (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL,
  style_family TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  vector_json TEXT,
  evidence_coverage REAL NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_style_family ON style_signatures(style_family);
"""


def connect(path: str | Path = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def upsert_style_signature(conn: sqlite3.Connection, *, signature_id: str, source_id: str, style_family: str, payload: dict[str, Any], vector: Sequence[float] | None = None, evidence_coverage: float = 0.0) -> None:
    conn.execute(
        """INSERT INTO style_signatures(id,source_id,style_family,payload_json,vector_json,evidence_coverage)
           VALUES(?,?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET source_id=excluded.source_id, style_family=excluded.style_family,
             payload_json=excluded.payload_json, vector_json=excluded.vector_json, evidence_coverage=excluded.evidence_coverage""",
        (signature_id, source_id, style_family, json.dumps(payload, sort_keys=True), json.dumps(list(vector)) if vector is not None else None, float(evidence_coverage)),
    )
    conn.commit()


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot=sum(x*y for x,y in zip(a,b)); na=sqrt(sum(x*x for x in a)); nb=sqrt(sum(y*y for y in b))
    return dot/(na*nb) if na and nb else 0.0


def retrieve_similar(conn: sqlite3.Connection, query_vector: Sequence[float], *, limit: int = 10, style_family: str | None = None) -> list[dict[str, Any]]:
    if style_family:
        rows=conn.execute("SELECT * FROM style_signatures WHERE style_family=?", (style_family,)).fetchall()
    else:
        rows=conn.execute("SELECT * FROM style_signatures").fetchall()
    scored=[]
    for row in rows:
        if row["vector_json"] is None:
            continue
        vector=json.loads(row["vector_json"])
        scored.append({
            "id":row["id"],"source_id":row["source_id"],"style_family":row["style_family"],
            "similarity":round(_cosine(query_vector,vector),6),
            "evidence_coverage":row["evidence_coverage"],"payload":json.loads(row["payload_json"]),
        })
    return sorted(scored, key=lambda x:(x["similarity"],x["evidence_coverage"]), reverse=True)[:limit]
