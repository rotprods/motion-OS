from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.qa.primitive_fixture_runner import build_fixture_specs, contract_evidence, qualification_plan, write_fixture_specs
from src.qa.primitive_qualification import LegacyAggregateClaim, PrimitiveQualificationLedger


def _json_dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')


def cmd_plan(args: argparse.Namespace) -> int:
    payload = qualification_plan()
    if args.out:
        _json_dump(Path(args.out), payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_materialize(args: argparse.Namespace) -> int:
    paths = write_fixture_specs(args.out_dir)
    payload = {
        'schema': 'motion-os.primitive-fixture-materialization/v1',
        'output_dir': str(Path(args.out_dir)),
        'fixture_count': len(paths),
        'files': [str(path) for path in paths],
    }
    manifest = Path(args.out_dir) / 'manifest.json'
    _json_dump(manifest, payload)
    print(json.dumps({'fixture_count': len(paths), 'manifest': str(manifest)}, indent=2))
    return 0


def cmd_contract(args: argparse.Namespace) -> int:
    specs = build_fixture_specs()
    evidence = [contract_evidence(spec, test_run_id=args.test_run_id) for spec in specs]
    ledger = PrimitiveQualificationLedger(evidence=evidence)
    legacy = LegacyAggregateClaim(
        source_ref='state/convergence_checkpoints.json#CP25',
        registered_count=45,
        verified_count=15,
        quarantined_count=30,
    )
    payload = {
        'schema': 'motion-os.primitive-contract-evidence/v1',
        'test_run_id': args.test_run_id,
        'evidence': [item.__dict__ for item in ledger.evidence],
        'report': ledger.report(legacy_claim=legacy),
    }
    _json_dump(Path(args.out), payload)
    print(json.dumps({
        'evidence_count': len(evidence),
        'primitive_counts': payload['report']['primitive_counts'],
        'renderer_cases': payload['report']['renderer_cases'],
        'empirical_authority': payload['report']['empirical_authority'],
        'out': args.out,
    }, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='MOTION.OS primitive production qualification tooling')
    sub = parser.add_subparsers(dest='command', required=True)

    plan = sub.add_parser('plan', help='show the live 45×renderer qualification plan')
    plan.add_argument('--out')
    plan.set_defaults(func=cmd_plan)

    materialize = sub.add_parser('materialize', help='write canonical fixture JSON for every primitive/renderer case')
    materialize.add_argument('--out-dir', required=True)
    materialize.set_defaults(func=cmd_materialize)

    contract = sub.add_parser('contract-evidence', help='emit contract-only evidence for all canonical fixture cases')
    contract.add_argument('--test-run-id', required=True)
    contract.add_argument('--out', required=True)
    contract.set_defaults(func=cmd_contract)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
