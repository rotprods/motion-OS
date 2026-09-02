from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark import benchmark_live, benchmark_synthetic
from .engine import SemanticKnowledgePlane
from .server import serve


def _print(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AVE + MOTION.OS local semantic knowledge plane")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="verify Ollama, model and Qdrant collection contract")
    index = sub.add_parser("index", help="chunk, embed and incrementally index one or more repositories")
    index.add_argument("--repo", action="append", required=True, help="local repository path; repeatable")
    graphify = sub.add_parser("graphify", help="materialize semantic neighbor edges in Qdrant payload")
    graphify.add_argument("--repo-id", action="append", default=[])
    graphify.add_argument("--neighbors", type=int, default=8)
    graphify.add_argument("--min-score", type=float, default=0.15)
    query = sub.add_parser("query", help="query /cos-graph-engine pipeline")
    query.add_argument("query")
    query.add_argument("--repo-id", action="append", default=[])
    query.add_argument("--limit", type=int, default=10)
    server = sub.add_parser("serve", help="serve /graphify and /cos-graph-engine on loopback")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8791)
    bench = sub.add_parser("benchmark", help="run deterministic core benchmark and optional live service benchmark")
    bench.add_argument("--live", action="store_true")
    bench.add_argument("--iterations", type=int, default=8)
    bench.add_argument("--route-multiplier", type=int, default=32)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    plane = SemanticKnowledgePlane()
    if args.command == "doctor":
        _print(plane.doctor())
        return
    if args.command == "index":
        _print({"reports": [plane.index_repository(Path(repo)) for repo in args.repo]})
        return
    if args.command == "graphify":
        _print(plane.graphify(repo_ids=args.repo_id or None, neighbors=args.neighbors, min_semantic_score=args.min_score))
        return
    if args.command == "query":
        _print(plane.cos_graph_engine(args.query, limit=args.limit, repo_ids=args.repo_id or None))
        return
    if args.command == "serve":
        if args.host not in {"127.0.0.1", "localhost", "::1"}:
            raise SystemExit("refusing non-loopback bind; place an authenticated proxy in front explicitly")
        serve(plane, host=args.host, port=args.port)
        return
    if args.command == "benchmark":
        report = {
            "synthetic": benchmark_synthetic(route_multiplier=args.route_multiplier),
            "live": benchmark_live(plane, iterations=args.iterations) if args.live else {"status": "NOT_EXECUTED"},
        }
        report["passed"] = bool(report["synthetic"].get("passed")) and (not args.live or bool(report["live"].get("passed")))
        _print(report)
        return


if __name__ == "__main__":
    main()
