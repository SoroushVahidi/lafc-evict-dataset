#!/usr/bin/env python3
"""CLI entry point for the LAFC-Evict Tier-1 closed-loop production harness.

Modes:

  --preflight
      Non-destructive. Verifies the 230-run plan, trace paths/hashes,
      simulator branch/HEAD/dependency-file cleanliness, and split/window
      definitions. Never executes a real closed-loop replay. Exits nonzero
      if any gate fails.

  --run [--resume] [--retry-failed] [--run-dir PATH]
      Executes the approved 230-run Tier-1 production plan and writes
      durable outputs/provenance under outputs/<RUN_ID>/. Without
      --run-dir, a new immutable run directory is created. This mode is
      NOT invoked by the implementation/validation task that created this
      file -- it exists so a future, explicitly-approved launch has a real
      command to run.

  --validate --run-dir PATH
      Re-checks a completed (or partial) run directory against every
      programmatic validity gate, without re-executing anything.

Tier 2 (evict_value_v1) and continuation-policy sensitivity are out of
scope for this script; there is no code path here that can reach them
(see tier1_core.assert_no_learned_policy and FORBIDDEN_SIMULATOR_MODULES).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tier1_core  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true", help="Run non-destructive preflight checks only.")
    mode.add_argument("--run", action="store_true", help="Execute the approved 230-run Tier-1 plan.")
    mode.add_argument("--validate", action="store_true", help="Validate a completed run directory.")
    parser.add_argument("--run-dir", type=str, default=None, help="Run directory (required for --validate; optional resume target for --run).")
    parser.add_argument("--resume", action="store_true", help="Resume an existing --run-dir, skipping already-complete executions.")
    parser.add_argument("--retry-failed", action="store_true", help="With --resume, also retry executions previously recorded as failed.")
    parser.add_argument("--json", action="store_true", help="Print the full report as JSON in addition to the summary lines.")
    args = parser.parse_args(argv)

    if args.preflight:
        ok, report = tier1_core.run_preflight()
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True, default=str))
        else:
            for g in report["gates"]:
                status = "PASS" if g["passed"] else "FAIL"
                line = f"[{status}] {g['name']}"
                if g["detail"]:
                    line += f" -- {g['detail']}"
                print(line)
        print(f"TIER1_PREFLIGHT: {'PASS' if ok else 'FAIL'}")
        print(f"PLANNED_EXECUTIONS: {report['plan_summary']['total_executions']}")
        print("PRODUCTION_RUN_STARTED: NO")
        return 0 if ok else 1

    if args.run:
        if args.retry_failed and not args.resume:
            parser.error("--retry-failed requires --resume")
        if args.run_dir:
            run_dir = Path(args.run_dir)
            if not args.resume:
                parser.error("--run-dir without --resume would refuse to reuse a directory; pass --resume explicitly to continue it, or omit --run-dir to create a new one.")
            run_dir.mkdir(parents=True, exist_ok=True)
        else:
            run_dir = tier1_core.new_run_dir()
        manifest = tier1_core.run_production(
            run_dir, resume=args.resume, retry_failed=args.retry_failed,
            command_line=" ".join(sys.argv),
        )
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0 if manifest["run_valid"] else 1

    if args.validate:
        if not args.run_dir:
            parser.error("--validate requires --run-dir")
        ok, report = tier1_core.run_validate(Path(args.run_dir))
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True, default=str))
        else:
            for g in report["gates"]:
                status = "PASS" if g["passed"] else "FAIL"
                line = f"[{status}] {g['name']}"
                if g["detail"]:
                    line += f" -- {g['detail']}"
                print(line)
        print(f"TIER1_VALIDATE: {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
