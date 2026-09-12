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
from recruiter import RecruiterManager


def get_environment_info():
    is_gemini = True  # Antigravity IDE uses Gemini 3.8 Flash
    return {
        "model_runtime": "Gemini (Google Antigravity IDE / Gemini 3.8 Flash)",
        "skill_handling_mode": "Gemini Transpilation Mode (.skills/gemini_adapted/)",
        "token_compaction_threshold": "100,000 active tokens",
        "verification_architecture": "CYCLIC MULTI-AGENT MESH (5 Interlocking Loops)",
        "recruiter_mode": "Chief Organizational Manager (Zero Synthetic Files — 100% Repository Sourced)"
    }


def show_status():
    cm = ContextManager()
    env = get_environment_info()

    print("=" * 75)
    print("  STRATEGIST: BUSINESS-FIRST AUTONOMOUS AGENT ECOSYSTEM")
    print("=" * 75)
    print(f"Host Model/Runtime       : {env['model_runtime']}")
    print(f"Skill Handling Mode       : {env['skill_handling_mode']}")
    print(f"Recruiter Policy          : {env['recruiter_mode']}")
    print(f"Context Compaction Limit  : {env['token_compaction_threshold']}")
    print(f"Current Phase             : {cm.session_state.get('phase', 'discovery').upper()}")
    print(f"Active Agents             : {', '.join(cm.session_state.get('active_agents', []))}")
    print(f"Last Active Task          : {cm.session_state.get('last_active_task', 'N/A')}")
    print("-" * 75)

    recruited_dir = AGENTS_DIR / "recruited"
    recruited_count = len(list(recruited_dir.glob("*.md"))) if recruited_dir.exists() else 0
    print(f"Recruited Real Agents     : {recruited_count} agents installed from claude-skills")
    
    mesh_path = STATE_DIR / "org_mesh.json"
    if mesh_path.exists():
        with open(mesh_path, "r", encoding="utf-8") as f:
            mesh = json.load(f)
        print(f"Organizational Mesh Loops : {len(mesh.get('execution_loops', {}))} active cyclic feedback loops")

    tracker = cm.session_state.get("token_tracker", {})
    print(f"Token Utilization         : {tracker.get('active_tokens', 0)} / {tracker.get('compaction_threshold', 100000)} tokens")
    print(f"Conversation Turns        : {tracker.get('turn_count', 0)} / {tracker.get('max_turns_before_compaction', 20)} turns")
    print("-" * 75)

    audit = cm.loop_audit
    print(f"Loop A (TDD) Retries      : {audit.get('loop_a_tdd', {}).get('iteration_count', 0)} / {audit.get('max_loop_retries', 5)}")
    print(f"Loop B (DevOps) Retries   : {audit.get('loop_b_devops', {}).get('iteration_count', 0)} / {audit.get('max_loop_retries', 5)}")
    print(f"Circuit Breaker Tripped   : {'YES - HALTED' if audit.get('circuit_breaker_triggered') else 'NO (Nominal)'}")
    print("-" * 75)

    print("Ground Truth Docs Status:")
    for doc in ["00_PROBLEM_AUDIT.md", "01_ECOSYSTEM_TOPOLOGY.md", "02_GROUND_TRUTH_SRS.md", "03_TEST_ACCEPTANCE.md"]:
        p = DOCS_DIR / doc
        exists = "EXISTS" if p.exists() else "MISSING"
        size = f"{p.stat().st_size} bytes" if p.exists() else "0 bytes"
        print(f"  - docs/{doc:<25}: [{exists}] ({size})")
    print("=" * 75)


def show_mesh():
    mesh_path = STATE_DIR / "org_mesh.json"
    if not mesh_path.exists():
        rm = RecruiterManager()
        rm.build_org_mesh()

    with open(mesh_path, "r", encoding="utf-8") as f:
        mesh = json.load(f)

    print("=" * 75)
    print("  STRATEGIST ORGANIZATIONAL MESH & CYCLIC LOOP TOPOLOGY")
    print("=" * 75)
    print(f"Policy: {mesh.get('recruiter_mode')}")
    print(f"Source: {mesh.get('source_repo')}")
    print(f"Total Agents in Mesh: {mesh.get('total_agents')}\n")

    print("[EXECUTION LOOPS]")
    for lid, linfo in mesh.get("execution_loops", {}).items():
        print(f"▶ {linfo['name']}")
        print(f"  Description: {linfo['description']}")
        if "workers" in linfo:
            print(f"  Workers    : {', '.join(linfo['workers'])}")
        if "adversaries" in linfo:
            print(f"  Adversaries: {', '.join(linfo['adversaries'])}")
        if "feedback_peers" in linfo:
            print(f"  Peers      : {', '.join(linfo['feedback_peers'])}")
        print()

    print("[ACTIVE AGENT ROSTER]")
    for aid, ameta in mesh.get("agents", {}).items():
        inst = "✓ Installed" if ameta.get("installed") else "✗ Missing"
        print(f"  [{inst}] {aid:<25} : {ameta['title']} ({ameta['domain']})")
    print("=" * 75)


def main():
    parser = argparse.ArgumentParser(description="Strategist Orchestrator CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Display ecosystem and agent state")
    subparsers.add_parser("transpile-test", help="Test skill transpiler")
    subparsers.add_parser("mesh", help="Display organizational agent mesh and feedback loops")
    
    recruit_parser = subparsers.add_parser("recruit", help="Recruit real agents from claude-skills")
    recruit_parser.add_argument("--all", action="store_true", help="Recruit all core agents from repository")
    recruit_parser.add_argument("--agent", help="Recruit a specific agent by ID")

    compact_parser = subparsers.add_parser("compact", help="Trigger context state compaction")
    compact_parser.add_argument("--summary", default="Manual compaction checkpoint", help="Summary for checkpoint")

    bounce_parser = subparsers.add_parser("bounce", help="Simulate a loop retry bounce")
    bounce_parser.add_argument("loop", choices=["a", "b"], help="Loop A (TDD) or Loop B (DevOps)")
    bounce_parser.add_argument("--reason", required=True, help="Reason for failure bounce")

    args = parser.parse_args()

    if args.command == "status" or not args.command:
        show_status()
    elif args.command == "mesh":
        show_mesh()
    elif args.command == "transpile-test":
        run_self_test()
    elif args.command == "recruit":
        rm = RecruiterManager()
        if args.agent:
            res = rm.recruit_agent(args.agent)
            print(f"Successfully recruited {res['title']} -> {res['active_path']}")
        else:
            rm.recruit_all_agents()
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
