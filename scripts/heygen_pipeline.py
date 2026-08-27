#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.content.content_factory import preflight_manifest
from src.content.integrity import seal_manifest, verify_manifest
from src.content.provenance_chain import attach_provenance_chain, verify_provenance_chain, downstream_handoff_record
from src.content.schema_migrations import migrate
from src.avatar.heygen_adapter import compile_request
from src.avatar.render_guard import SpendPolicy, authorize_render
from src.avatar.render_ledger import RenderLedger
from src.avatar.transactional_store import SQLiteTransactionalRenderStore

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILES = ROOT / "config" / "avatar_profiles.json"
DEFAULT_RENDER_POLICY = ROOT / "config" / "phase06_render_policy.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description="MOTION.OS /heygen resilient preflight + deterministic authority compiler")
    p.add_argument("manifest", type=Path, help="avatar content manifest JSON")
    p.add_argument("--source-pack", type=Path, default=None, help="normalized untrusted SourcePack JSON for provenance chaining")
    p.add_argument("--profiles", type=Path, default=DEFAULT_PROFILES)
    p.add_argument("--render-policy", type=Path, default=DEFAULT_RENDER_POLICY)
    p.add_argument("--profile", default="heygen_rot_canonical_v1")
    p.add_argument("--title", default="MOTION.OS avatar render")
    p.add_argument("--motion-prompt", default=None)
    p.add_argument("--migrate", action="store_true", help="migrate manifest to current schema before validation")
    p.add_argument("--seal-out", type=Path, default=None, help="write integrity-sealed manifest")
    p.add_argument("--authorize-render", action="store_true", help="explicitly authorize a paid render intent")
    p.add_argument("--estimated-credits", type=float, default=None)
    p.add_argument("--spent-today", type=float, default=0.0)
    p.add_argument("--concurrent-renders", type=int, default=0)
    p.add_argument("--ledger", type=Path, default=None, help="append authorization to legacy hash-chain JSONL ledger")
    p.add_argument("--authority-db", type=Path, default=None, help="SQLite transactional authority DB for single-host multiprocess execution")
    p.add_argument("--worker-id", default="heygen-cli")
    p.add_argument("--lease-ttl", type=float, default=30.0)
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    manifest = load_json(args.manifest)
    if args.migrate:
        manifest = migrate(manifest)
    source_pack = load_json(args.source_pack) if args.source_pack else None
    if source_pack:
        manifest = attach_provenance_chain(source_pack, manifest)

    profiles = load_json(args.profiles)["profiles"]
    profile = profiles[args.profile]
    result = preflight_manifest(manifest, profile)

    sealed = seal_manifest(manifest) if result.ok else None
    if sealed and args.seal_out:
        args.seal_out.write_text(json.dumps(sealed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    provenance_verified = bool(source_pack and sealed and verify_provenance_chain(source_pack, sealed))
    report = {
        "command": "/heygen",
        "preflight": {
            "ok": result.ok,
            "errors": list(result.errors),
            "warnings": list(result.warnings),
            "estimated_duration_s": result.estimated_duration_s,
        },
        "integrity": {
            "sealed": bool(sealed),
            "verified": bool(sealed and verify_manifest(sealed)),
            "replay_fingerprint": (sealed or {}).get("integrity", {}).get("replay_fingerprint"),
        },
        "provenance": {
            "attached": bool(source_pack),
            "verified": provenance_verified,
            "root": (sealed or {}).get("provenance_chain", {}).get("root"),
        },
        "downstream_handoff": None,
        "render_intent": None,
        "provider_request": None,
    }

    if result.ok:
        report["provider_request"] = compile_request(manifest, profile, title=args.title, motion_prompt=args.motion_prompt)
        if source_pack and sealed:
            report["downstream_handoff"] = downstream_handoff_record(sealed)

    if args.authorize_render:
        if not result.ok:
            raise SystemExit("cannot authorize render: preflight failed")
        if source_pack and not provenance_verified:
            raise SystemExit("cannot authorize render: provenance chain verification failed")
        policy_doc = load_json(args.render_policy)["render_defaults"]
        policy = SpendPolicy(
            max_credits_per_render=float(policy_doc["max_credits_per_render"]),
            max_credits_per_day=float(policy_doc["max_credits_per_day"]),
            max_concurrent_renders=int(policy_doc["max_concurrent_renders"]),
            max_retries=int(policy_doc.get("max_retries", 1)),
        )
        intent = authorize_render(
            content_id=manifest["content_id"],
            profile_id=args.profile,
            script=manifest["script_tts_text"],
            explicit_authorization=True,
            preflight_ok=result.ok,
            estimated_credits=args.estimated_credits,
            spent_today=args.spent_today,
            concurrent_renders=args.concurrent_renders,
            policy=policy,
        )
        report["render_intent"] = intent.to_dict()
        if args.ledger:
            ledger = RenderLedger(args.ledger)
            known = ledger.latest_intents()
            if intent.intent_id in known:
                raise RuntimeError("equivalent render intent already exists in ledger; reconcile instead")
            ledger.record_intent(intent, "AUTHORIZED")
        if args.authority_db:
            store = SQLiteTransactionalRenderStore(args.authority_db)
            lease = store.acquire_lease(intent.intent_id, args.worker_id, ttl_s=args.lease_ttl)
            try:
                existing = store.get_intent(intent.intent_id)
                if existing is not None:
                    raise RuntimeError("equivalent render intent already exists in transactional authority; reconcile instead")
                store.put_intent(intent, lease)
            finally:
                store.release_lease(lease)

    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
