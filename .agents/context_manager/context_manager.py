#!/usr/bin/env python3
"""
Context Manager utility for Strategist.
Handles token tracking, memory graph updates, compaction triggers,
temporary condensed memory persistence, and agent instance cycling.
"""

import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

STATE_DIR = Path(__file__).resolve().parent.parent.parent / ".state"
COMPACTION_TOKEN_THRESHOLD = 100000
MAX_TURNS_BEFORE_COMPACTION = 20
CIRCUIT_BREAKER_MAX_RETRIES = 5


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for a given text.
    Standard frontier model heuristic: ~4 characters per token or ~0.75 words per token.
    """
    if not text:
        return 0
    char_estimate = len(text) / 4.0
    word_estimate = len(text.split()) / 0.75
    return max(1, math.ceil((char_estimate + word_estimate) / 2.0))


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class ContextManager:
    def __init__(self, state_dir: Path = STATE_DIR):
        self.state_dir = Path(state_dir)
        self.memory_graph_path = self.state_dir / "memory_graph.json"
        self.session_state_path = self.state_dir / "session_state.json"
        self.loop_audit_path = self.state_dir / "loop_audit.json"

        self.memory_graph = load_json(self.memory_graph_path, {
            "version": "1.0",
            "project_name": "Strategist",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "decisions_made": [],
            "open_questions": [],
            "eliminated_paths": []
        })
        self.session_state = load_json(self.session_state_path, {
            "session_id": "session_bootstrap_001",
            "phase": "discovery",
            "host_model_mode": "gemini",
            "active_agents": ["context_manager", "business_analyst"],
            "token_tracker": {
                "active_tokens": 0,
                "compaction_threshold": COMPACTION_TOKEN_THRESHOLD,
                "turn_count": 0,
                "max_turns_before_compaction": MAX_TURNS_BEFORE_COMPACTION
            },
            "last_active_task": "Awaiting core business problem description from user",
            "checkpoints": [],
            "temporary_condensed_memory": None,
            "active_conversation": []
        })
        self.loop_audit = load_json(self.loop_audit_path, {
            "max_loop_retries": CIRCUIT_BREAKER_MAX_RETRIES,
            "circuit_breaker_triggered": False,
            "current_ticket": None,
            "loop_a_tdd": {"iteration_count": 0, "pass_status": False, "bounce_history": []},
            "loop_b_devops": {"iteration_count": 0, "pass_status": False, "bounce_history": []}
        })

    def record_turn(self, estimated_tokens: int = 1500) -> Dict[str, Any]:
        """Record a turn and update estimated token utilization."""
        tracker = self.session_state.setdefault("token_tracker", {})
        tracker["turn_count"] = tracker.get("turn_count", 0) + 1
        tracker["active_tokens"] = tracker.get("active_tokens", 0) + estimated_tokens

        needs_compaction = (
            tracker["active_tokens"] >= tracker.get("compaction_threshold", COMPACTION_TOKEN_THRESHOLD)
            or tracker["turn_count"] >= tracker.get("max_turns_before_compaction", MAX_TURNS_BEFORE_COMPACTION)
        )

        save_json(self.session_state_path, self.session_state)
        return {
            "turn_count": tracker["turn_count"],
            "active_tokens": tracker["active_tokens"],
            "needs_compaction": needs_compaction
        }

    def record_interaction(self, agent: str, role: str, content: str) -> Dict[str, Any]:
        """
        Record a rich interaction message, computing real tokens and tracking conversation history.
        """
        tokens = estimate_tokens(content)
        conv = self.session_state.setdefault("active_conversation", [])
        conv.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": agent,
            "role": role,
            "tokens": tokens,
            "snippet": content[:160] + "..." if len(content) > 160 else content
        })

        return self.record_turn(estimated_tokens=tokens)

    def add_decision(self, decision: str) -> None:
        """Add an immutable architectural or business decision."""
        if decision not in self.memory_graph["decisions_made"]:
            self.memory_graph["decisions_made"].append(decision)
            self.memory_graph["last_updated"] = datetime.now(timezone.utc).isoformat()
            save_json(self.memory_graph_path, self.memory_graph)

    def add_open_question(self, question: str) -> None:
        """Add an open question awaiting user confirmation."""
        if question not in self.memory_graph["open_questions"]:
            self.memory_graph["open_questions"].append(question)
            self.memory_graph["last_updated"] = datetime.now(timezone.utc).isoformat()
            save_json(self.memory_graph_path, self.memory_graph)

    def resolve_question(self, question: str) -> None:
        """Remove question once resolved."""
        if question in self.memory_graph["open_questions"]:
            self.memory_graph["open_questions"].remove(question)
            self.memory_graph["last_updated"] = datetime.now(timezone.utc).isoformat()
            save_json(self.memory_graph_path, self.memory_graph)

    def add_eliminated_path(self, path_description: str) -> None:
        """Record an explicitly rejected or eliminated solution/path."""
        if path_description not in self.memory_graph["eliminated_paths"]:
            self.memory_graph["eliminated_paths"].append(path_description)
            self.memory_graph["last_updated"] = datetime.now(timezone.utc).isoformat()
            save_json(self.memory_graph_path, self.memory_graph)

    def record_loop_bounce(self, loop_type: str, reason: str, diff_or_report: Optional[str] = None) -> bool:
        """
        Record a failure bounce in Loop A (TDD) or Loop B (DevOps).
        Returns True if circuit breaker is triggered (>= 5 consecutive rejections).
        """
        key = "loop_a_tdd" if "a" in loop_type.lower() else "loop_b_devops"
        loop_data = self.loop_audit.setdefault(key, {"iteration_count": 0, "bounce_history": []})
        loop_data["iteration_count"] = loop_data.get("iteration_count", 0) + 1

        entry = {
            "iteration": loop_data["iteration_count"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "details": diff_or_report
        }
        loop_data["bounce_history"].append(entry)

        if loop_data["iteration_count"] >= self.loop_audit.get("max_loop_retries", CIRCUIT_BREAKER_MAX_RETRIES):
            self.loop_audit["circuit_breaker_triggered"] = True
            save_json(self.loop_audit_path, self.loop_audit)
            return True

        save_json(self.loop_audit_path, self.loop_audit)
        return False

    def reset_loop(self, loop_type: str) -> None:
        """Reset iteration counter upon pass."""
        key = "loop_a_tdd" if "a" in loop_type.lower() else "loop_b_devops"
        if key in self.loop_audit:
            self.loop_audit[key]["iteration_count"] = 0
            self.loop_audit[key]["pass_status"] = True
        self.loop_audit["circuit_breaker_triggered"] = False
        save_json(self.loop_audit_path, self.loop_audit)

    def generate_condensed_memory(self, summary_note: str, task_objective: str) -> Dict[str, Any]:
        """
        Extract and distill a high-density, condensed temporary memory representation
        from the verbose active thread, immutable memory graph, and task context.
        """
        tracker = self.session_state.get("token_tracker", {})
        active_tokens = tracker.get("active_tokens", 0)
        turn_count = tracker.get("turn_count", 0)

        condensed = {
            "compaction_timestamp": datetime.now(timezone.utc).isoformat(),
            "source_tokens_compacted": active_tokens,
            "source_turns_compacted": turn_count,
            "summary_note": summary_note,
            "last_active_task": task_objective,
            "key_decisions": list(self.memory_graph.get("decisions_made", [])),
            "pending_questions": list(self.memory_graph.get("open_questions", [])),
            "eliminated_paths": list(self.memory_graph.get("eliminated_paths", [])),
            "context_digest": (
                f"Distilled session checkpoint: {turn_count} turns compacted from {active_tokens:,} tokens. "
                f"Core focus: {task_objective}. "
                f"{len(self.memory_graph.get('decisions_made', []))} immutable decisions preserved."
            )
        }
        return condensed

    def compact_state(self, summary_note: str, task_objective: Optional[str] = None) -> Dict[str, Any]:
        """Perform proactive compaction when token/turn threshold is reached."""
        obj = task_objective or self.session_state.get("last_active_task", "Continue solution development")
        condensed = self.generate_condensed_memory(summary_note, obj)

        checkpoint = {
            "timestamp": condensed["compaction_timestamp"],
            "turn_count": condensed["source_turns_compacted"],
            "tokens_compacted": condensed["source_tokens_compacted"],
            "summary": summary_note,
            "condensed_digest": condensed["context_digest"]
        }
        self.session_state.setdefault("checkpoints", []).append(checkpoint)

        # Store temporary condensed memory
        self.session_state["temporary_condensed_memory"] = condensed
        self.session_state["last_active_task"] = obj

        # Reset active working memory (terminate verbose history)
        self.session_state["active_conversation"] = []
        self.session_state.setdefault("token_tracker", {})["turn_count"] = 0
        self.session_state["token_tracker"]["active_tokens"] = 0

        save_json(self.session_state_path, self.session_state)
        save_json(self.memory_graph_path, self.memory_graph)
        return condensed

    def cycle_agent_instance(
        self,
        retiring_agent: str,
        next_agent: str,
        next_persona_prompt: str,
        task_objective: str,
        summary_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the mandatory Context Manager Agent cycling protocol:
        1. Compiles and saves compressed temporary memory to .state/session_state.json
        2. Updates persistent .state/memory_graph.json
        3. Terminates verbose agent instance (clearing conversational debris)
        4. Re-instantiates fresh agent instance injected with:
           (a) Base persona prompt
           (b) Consolidated memory graph
           (c) Temporary condensed memory snapshot
           (d) Last active task objective
        """
        note = summary_note or f"Compaction cycle from @{retiring_agent} to @{next_agent}"
        condensed_memory = self.compact_state(note, task_objective)

        # Switch active agents
        self.session_state["active_agents"] = [
            a for a in self.session_state.get("active_agents", []) if a != retiring_agent
        ]
        if next_agent not in self.session_state["active_agents"]:
            self.session_state["active_agents"].append(next_agent)
        save_json(self.session_state_path, self.session_state)

        # Build injected context payload for the next agent
        injected_prompt = self.build_injected_prompt_for_agent(
            base_persona_prompt=next_persona_prompt,
            condensed_memory=condensed_memory,
            task_objective=task_objective
        )
        injected_tokens = estimate_tokens(injected_prompt)

        # Seed new instance with the compact context
        self.session_state["token_tracker"]["active_tokens"] = injected_tokens
        self.session_state["token_tracker"]["turn_count"] = 1
        save_json(self.session_state_path, self.session_state)

        return {
            "status": "SUCCESSFULLY_CYCLED",
            "retiring_agent": retiring_agent,
            "next_agent": next_agent,
            "tokens_compacted": condensed_memory["source_tokens_compacted"],
            "new_instance_active_tokens": injected_tokens,
            "compression_ratio": (
                f"{((1 - (injected_tokens / max(1, condensed_memory['source_tokens_compacted']))) * 100):.1f}% reduction"
            ),
            "temporary_condensed_memory": condensed_memory,
            "injected_prompt": injected_prompt
        }

    def build_injected_prompt_for_agent(
        self,
        base_persona_prompt: str,
        condensed_memory: Dict[str, Any],
        task_objective: str
    ) -> str:
        """
        Injects:
        (a) Base persona prompt
        (b) Consolidated memory_graph.json
        (c) Temporary condensed memory snapshot
        (d) Last active task objective
        """
        decisions_str = "\n".join(f"  - {d}" for d in condensed_memory.get("key_decisions", [])) or "  - None"
        eliminated_str = "\n".join(f"  - {e}" for e in condensed_memory.get("eliminated_paths", [])) or "  - None"
        questions_str = "\n".join(f"  - {q}" for q in condensed_memory.get("pending_questions", [])) or "  - None"

        injected_block = f"""
================================================================================
>>> INJECTED CONSOLIDATED STATE & CONDENSED MEMORY SNAPSHOT <<<
Context Manager: Active Session Compaction Applied.
Source Tokens Compacted: {condensed_memory.get('source_tokens_compacted', 0):,} tokens.
Timestamp: {condensed_memory.get('compaction_timestamp')}

[1. CONSOLIDATED MEMORY GRAPH (IMMUTABLE GROUND TRUTH)]
Decisions Made:
{decisions_str}

Eliminated Paths (Anti-Solution Bias):
{eliminated_str}

Pending Open Questions:
{questions_str}

[2. TEMPORARY CONDENSED MEMORY DIGEST]
{condensed_memory.get('context_digest')}

[3. ACTIVE TASK OBJECTIVE]
Target: {task_objective}
================================================================================
"""
        return f"{base_persona_prompt.strip()}\n\n{injected_block.strip()}"


if __name__ == "__main__":
    cm = ContextManager()
    print("Strategist Context Manager Initialized.")
    print(f"Memory Graph: {len(cm.memory_graph['decisions_made'])} decisions, {len(cm.memory_graph['open_questions'])} open questions.")
    print(f"Token Tracker: {cm.session_state['token_tracker']}")
    print(f"Circuit Breaker Status: {cm.loop_audit['circuit_breaker_triggered']}")
