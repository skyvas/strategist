#!/usr/bin/env python3
"""
Strategist Master Orchestrator CLI.
Coordinates the autonomous multi-agent development engine, monitors state, and enforces cyclic verification.
"""

import argparse
import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATE_DIR = BASE_DIR / ".state"
DOCS_DIR = BASE_DIR / "docs"
AGENTS_DIR = BASE_DIR / ".agents"
SKILLS_DIR = BASE_DIR / ".skills"

sys.path.insert(0, str(AGENTS_DIR / "context_manager"))
sys.path.insert(0, str(AGENTS_DIR / "recruiter"))

from context_manager import ContextManager
from transpiler import run_self_test


def get_environment_info():
    # Detect environment based on available tools and env
    is_gemini = True  # Antigravity IDE uses Gemini 3.8 Flash
    return {
        "model_runtime": "Gemini (Google Antigravity IDE / Gemini 3.8 Flash)",
        "skill_handling_mode": "Gemini Transpilation Mode (.skills/gemini_adapted/)",
        "token_compaction_threshold": "100,000 active tokens",
        "verification_architecture": "CYCLIC (Swarm <-> QA Loop A & Swarm <-> DevOps Loop B)"
    }


def show_status():
    cm = ContextManager()
    env = get_environment_info()

    print("=" * 70)
    print("  STRATEGIST: BUSINESS-FIRST AUTONOMOUS AGENT ECOSYSTEM")
    print("=" * 70)
    print(f"Host Model/Runtime      : {env['model_runtime']}")
    print(f"Skill Handling Mode      : {env['skill_handling_mode']}")
    print(f"Context Compaction Limit : {env['token_compaction_threshold']}")
    print(f"Current Phase            : {cm.session_state.get('phase', 'discovery').upper()}")
    print(f"Active Agents            : {', '.join(cm.session_state.get('active_agents', []))}")
    print(f"Last Active Task         : {cm.session_state.get('last_active_task', 'N/A')}")
    print("-" * 70)
    
    tracker = cm.session_state.get("token_tracker", {})
    print(f"Token Utilization        : {tracker.get('active_tokens', 0)} / {tracker.get('compaction_threshold', 100000)} tokens")
    print(f"Conversation Turns       : {tracker.get('turn_count', 0)} / {tracker.get('max_turns_before_compaction', 20)} turns")
    print(f"Compacted Checkpoints    : {len(cm.session_state.get('checkpoints', []))}")
    print("-" * 70)

    audit = cm.loop_audit
    print(f"Loop A (TDD) Retries     : {audit.get('loop_a_tdd', {}).get('iteration_count', 0)} / {audit.get('max_loop_retries', 5)}")
    print(f"Loop B (DevOps) Retries  : {audit.get('loop_b_devops', {}).get('iteration_count', 0)} / {audit.get('max_loop_retries', 5)}")
    print(f"Circuit Breaker Tripped  : {'YES - HALTED' if audit.get('circuit_breaker_triggered') else 'NO (Nominal)'}")
    print("-" * 70)

    print("Ground Truth Docs Status:")
    for doc in ["00_PROBLEM_AUDIT.md", "01_ECOSYSTEM_TOPOLOGY.md", "02_GROUND_TRUTH_SRS.md", "03_TEST_ACCEPTANCE.md"]:
        p = DOCS_DIR / doc
        exists = "EXISTS" if p.exists() else "MISSING"
        size = f"{p.stat().st_size} bytes" if p.exists() else "0 bytes"
        print(f"  - docs/{doc:<25}: [{exists}] ({size})")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Strategist Orchestrator CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Display ecosystem and agent state")
    subparsers.add_parser("transpile-test", help="Test skill transpiler")
    
    compact_parser = subparsers.add_parser("compact", help="Trigger context state compaction")
    compact_parser.add_argument("--summary", default="Manual compaction checkpoint", help="Summary for checkpoint")

    bounce_parser = subparsers.add_parser("bounce", help="Simulate a loop retry bounce")
    bounce_parser.add_argument("loop", choices=["a", "b"], help="Loop A (TDD) or Loop B (DevOps)")
    bounce_parser.add_argument("--reason", required=True, help="Reason for failure bounce")

    args = parser.parse_args()

    if args.command == "status" or not args.command:
        show_status()
    elif args.command == "transpile-test":
        run_self_test()
    elif args.command == "compact":
        cm = ContextManager()
        checkpoint = cm.compact_state(args.summary)
        print(f"State compacted successfully: {checkpoint}")
    elif args.command == "bounce":
        cm = ContextManager()
        halted = cm.record_loop_bounce(args.loop, args.reason)
        print(f"Recorded bounce in Loop {args.loop.upper()}. Circuit breaker triggered: {halted}")


if __name__ == "__main__":
    main()
