#!/usr/bin/env python3
"""CLI for ODBE-Forge."""

from __future__ import annotations

import argparse
import json
import sys

from odbe_forge_v3 import ODBEForge


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ODBE-Forge hierarchical multi-LLM agent")
    parser.add_argument("task", nargs="?", help="Task for the agent hierarchy")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--backend", choices=["offline", "openai", "anthropic"], default=None)
    parser.add_argument("--allow-risky", action="store_true", help="Do not block restricted patterns")
    args = parser.parse_args(argv)

    task = args.task
    if not task:
        if not sys.stdin.isatty():
            task = sys.stdin.read().strip()
        else:
            parser.error("Provide a task argument or pipe text on stdin")

    backend = None
    backend_name = args.backend
    if backend_name:
        from odbe_forge_v3 import build_backend

        backend, _ = build_backend(backend_name)

    forge = ODBEForge(backend=backend, allow_risky=args.allow_risky)
    if backend_name:
        forge.backend_name = backend_name

    result = forge.run(task)

    if args.json:
        payload = {
            "backend": result.backend,
            "report": result.report,
            "deception": {
                "score": result.deception.score if result.deception else None,
                "flags": result.deception.flags if result.deception else [],
                "details": result.deception.details if result.deception else [],
            },
            "safety": {
                "allowed": result.safety.allowed if result.safety else None,
                "reasons": result.safety.reasons if result.safety else [],
            },
            "messages": [{"role": m.role, "content": m.content} for m in result.messages],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"# ODBE-Forge ({result.backend})\n")
        print(result.report)
        if result.deception:
            print("\n---")
            print(f"Deception score: {result.deception.score}")
            print(f"Flags: {', '.join(result.deception.flags) or 'none'}")
        if result.safety:
            print(f"Safety: {'allowed' if result.safety.allowed else 'blocked'}")

    return 0 if (result.safety is None or result.safety.allowed) else 2


if __name__ == "__main__":
    raise SystemExit(main())
