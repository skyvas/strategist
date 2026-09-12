#!/usr/bin/env python3
"""
Recruiter & Chief Organizational Manager for Strategist.
Extensively inspects https://github.com/alirezarezvani/claude-skills,
ingests real agent specifications and skills without synthetic file generation,
and architects the multi-agent organizational looping mesh.
"""

import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
AGENTS_DIR = BASE_DIR / ".agents"
RECRUITED_AGENTS_DIR = AGENTS_DIR / "recruited"
SKILLS_RAW_DIR = BASE_DIR / ".skills" / "raw_claude"
SKILLS_ADAPTED_DIR = BASE_DIR / ".skills" / "gemini_adapted"
STATE_DIR = BASE_DIR / ".state"

sys.path.insert(0, str(AGENTS_DIR / "recruiter"))
from transpiler import strip_claude_xml, transpile_tool_dict_to_gemini_json

REPO_RAW_BASE = "https://raw.githubusercontent.com/alirezarezvani/claude-skills/main/"
REPO_API_TREE = "https://api.github.com/repos/alirezarezvani/claude-skills/git/trees/main?recursive=1"

# Primary organizational roster from alirezarezvani/claude-skills
CORE_AGENT_ROSTER = {
    # 1. Strategic, Business & Project Orchestration
    "cs-bizops-orchestrator": {
        "repo_path": "business-operations/agents/cs-bizops-orchestrator.md",
        "domain": "business-operations",
        "title": "Business Operations & Process Lead",
        "loop": "Loop 1 (Problem Discovery & Wait-Time Audit)",
        "upstream": ["User", "Recruiter / Org Manager"],
        "downstream": ["cs-pm-orchestrator", "cs-engineering-lead"],
        "loop_peers": ["cs-pm-orchestrator"]
    },
    "cs-pm-orchestrator": {
        "repo_path": "project-management/agents/cs-pm-orchestrator.md",
        "domain": "project-management",
        "title": "Delivery & Project Management Orchestrator",
        "loop": "Loop 1 (Problem Discovery & Wait-Time Audit)",
        "upstream": ["cs-bizops-orchestrator"],
        "downstream": ["cs-engineering-lead", "cs-workflow-architect"],
        "loop_peers": ["cs-bizops-orchestrator"]
    },
    "cs-engineering-lead": {
        "repo_path": "docs/agents/cs-engineering-lead.md",
        "domain": "engineering",
        "title": "Engineering Lead & Technical System Architect",
        "loop": "Loop 2 (Architecture & System Design)",
        "upstream": ["cs-pm-orchestrator", "cs-bizops-orchestrator"],
        "downstream": ["cs-frontend-engineer", "cs-backend-engineer", "test-architect"],
        "loop_peers": ["cs-senior-engineer", "cs-workflow-architect"]
    },
    "cs-workflow-architect": {
        "repo_path": "docs/agents/cs-workflow-architect.md",
        "domain": "engineering",
        "title": "Workflow, DAG & State Machine Architect",
        "loop": "Loop 2 (Architecture & System Design)",
        "upstream": ["cs-engineering-lead"],
        "downstream": ["hub-coordinator", "cs-backend-engineer"],
        "loop_peers": ["cs-engineering-lead"]
    },

    # 2. Engineering Swarm (Workers)
    "cs-frontend-engineer": {
        "repo_path": "docs/agents/cs-frontend-engineer.md",
        "domain": "engineering",
        "title": "Frontend Engineering Orchestrator (UI/UX, Mobile, Tablet)",
        "loop": "Loop 3 (TDD Implementation Loop) & Loop 4 (Code Quality)",
        "upstream": ["cs-engineering-lead", "test-architect"],
        "downstream": ["test-debugger", "karpathy-reviewer"],
        "loop_peers": ["cs-backend-engineer", "test-architect", "karpathy-reviewer"]
    },
    "cs-backend-engineer": {
        "repo_path": "docs/agents/cs-backend-engineer.md",
        "domain": "engineering",
        "title": "Backend Engineering Orchestrator (API, Persistence, Microservices)",
        "loop": "Loop 3 (TDD Implementation Loop) & Loop 4 (Code Quality)",
        "upstream": ["cs-engineering-lead", "test-architect"],
        "downstream": ["test-debugger", "karpathy-reviewer", "devops-engineer"],
        "loop_peers": ["cs-frontend-engineer", "test-architect", "karpathy-reviewer"]
    },
    "cs-fullstack-engineer": {
        "repo_path": "docs/agents/cs-fullstack-engineer.md",
        "domain": "engineering",
        "title": "Fullstack Rapid Prototyper",
        "loop": "Loop 3 (TDD Implementation Loop)",
        "upstream": ["cs-engineering-lead"],
        "downstream": ["test-architect", "karpathy-reviewer"],
        "loop_peers": ["cs-senior-engineer"]
    },
    "cs-senior-engineer": {
        "repo_path": "docs/agents/cs-senior-engineer.md",
        "domain": "engineering",
        "title": "Senior Staff Engineer (Patterns & Resilience)",
        "loop": "Loop 4 (Code Quality & Review)",
        "upstream": ["cs-frontend-engineer", "cs-backend-engineer"],
        "downstream": ["devops-engineer", "hub-coordinator"],
        "loop_peers": ["karpathy-reviewer", "cs-engineering-lead"]
    },

    # 3. Checker Adversaries (Quality & Infrastructure)
    "test-architect": {
        "repo_path": "docs/agents/test-architect.md",
        "domain": "testing",
        "title": "Test Architect & Adversarial Strategy Lead",
        "loop": "Loop 3 (TDD Implementation Loop)",
        "upstream": ["cs-engineering-lead", "03_TEST_ACCEPTANCE.md"],
        "downstream": ["cs-frontend-engineer", "cs-backend-engineer", "test-debugger"],
        "loop_peers": ["cs-frontend-engineer", "cs-backend-engineer"]
    },
    "test-debugger": {
        "repo_path": "docs/agents/test-debugger.md",
        "domain": "testing",
        "title": "Runtime Test Debugger & Assertion Verifier",
        "loop": "Loop 3 (TDD Implementation Loop)",
        "upstream": ["cs-frontend-engineer", "cs-backend-engineer"],
        "downstream": ["test-architect", "karpathy-reviewer"],
        "loop_peers": ["test-architect"]
    },
    "karpathy-reviewer": {
        "repo_path": "docs/agents/karpathy-reviewer.md",
        "domain": "engineering",
        "title": "Adversarial Code Reviewer & Cleanliness Auditor",
        "loop": "Loop 4 (Code Quality & Review)",
        "upstream": ["cs-frontend-engineer", "cs-backend-engineer"],
        "downstream": ["cs-senior-engineer", "devops-engineer"],
        "loop_peers": ["cs-senior-engineer"]
    },
    "devops-engineer": {
        "repo_path": "docs/agents/devops-engineer.md",
        "domain": "devops",
        "title": "DevOps & Infrastructure Engineer",
        "loop": "Loop 5 (Runtime, Security & Infrastructure)",
        "upstream": ["karpathy-reviewer", "cs-senior-engineer"],
        "downstream": ["hub-coordinator", "Production Deployment"],
        "loop_peers": ["cs-backend-engineer", "hub-coordinator"]
    },

    # 4. Multi-Agent Governance & Handoff
    "hub-coordinator": {
        "repo_path": "docs/agents/hub-coordinator.md",
        "domain": "orchestration",
        "title": "AgentHub Multi-Agent Swarm Coordinator",
        "loop": "Orchestration & Convergence Governor",
        "upstream": ["Recruiter / Chief Org Manager", "devops-engineer"],
        "downstream": ["All Swarm Workers", "cs-handoff-author"],
        "loop_peers": ["Recruiter / Chief Org Manager"]
    },
    "cs-handoff-author": {
        "repo_path": "docs/agents/cs-handoff-author.md",
        "domain": "productivity",
        "title": "Context Compaction & Shift Handoff Author",
        "loop": "Continuity & Handoff Loop",
        "upstream": ["hub-coordinator", "Context Manager"],
        "downstream": ["Next Agent / Next Shift Lead"],
        "loop_peers": ["Context Manager"]
    }
}

KEY_SKILLS_TO_IMPORT = [
    # Business & Project Skills
    "business-operations/skills/process-mapper",
    "business-operations/skills/capacity-planner",
    "business-operations/skills/business-operations-skills",
    "project-management/skills/jira-expert",
    "project-management/skills/pm-skills",
    "project-management/skills/atlassian-templates",
    # Engineering & Coordination Skills
    "engineering/agenthub/skills/agenthub",
    "engineering/skills/agent-designer",
    "engineering/skills/agent-workflow-designer",
    "engineering/agent-harness/skills/agent-harness"
]


class RecruiterManager:
    def __init__(self):
        RECRUITED_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
        (SKILLS_RAW_DIR / "agents").mkdir(parents=True, exist_ok=True)
        (SKILLS_ADAPTED_DIR / "agents").mkdir(parents=True, exist_ok=True)
        STATE_DIR.mkdir(parents=True, exist_ok=True)

    def fetch_remote_file(self, rel_path: str) -> Optional[str]:
        url = REPO_RAW_BASE + rel_path
        req = urllib.request.Request(url, headers={"User-Agent": "Strategist-Recruiter/2.0"})
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                return resp.read().decode("utf-8")
        except Exception as e:
            sys.stderr.write(f"Failed to fetch {url}: {e}\n")
            return None

    def recruit_agent(self, agent_id: str) -> Dict[str, Any]:
        meta = CORE_AGENT_ROSTER.get(agent_id)
        if not meta:
            raise KeyError(f"Unknown agent '{agent_id}' in core roster.")

        raw_content = self.fetch_remote_file(meta["repo_path"])
        if not raw_content:
            raise RuntimeError(f"Could not download agent {agent_id} from {meta['repo_path']}")

        # 1. Save Raw Claude Agent
        raw_path = SKILLS_RAW_DIR / "agents" / f"{agent_id}.md"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(raw_content, encoding="utf-8")

        # 2. Transpile for Gemini Runtime
        gemini_content = strip_claude_xml(raw_content)
        adapted_path = SKILLS_ADAPTED_DIR / "agents" / f"{agent_id}.md"
        adapted_path.parent.mkdir(parents=True, exist_ok=True)
        adapted_path.write_text(gemini_content, encoding="utf-8")

        # 3. Mount into Active Recruited Agents (.agents/recruited/<agent_id>.md)
        active_path = RECRUITED_AGENTS_DIR / f"{agent_id}.md"
        
        # Inject org metadata header into the recruited active spec
        org_header = f"""<!--
ORGANIZATIONAL REGISTRY ENTRY
Agent ID    : {agent_id}
Title       : {meta['title']}
Domain      : {meta['domain']}
Loop Target : {meta['loop']}
Upstream    : {', '.join(meta['upstream'])}
Downstream  : {', '.join(meta['downstream'])}
Loop Peers  : {', '.join(meta['loop_peers'])}
Source Repo : {REPO_RAW_BASE}{meta['repo_path']}
-->

"""
        active_path.write_text(org_header + gemini_content, encoding="utf-8")

        return {
            "agent_id": agent_id,
            "title": meta["title"],
            "domain": meta["domain"],
            "loop": meta["loop"],
            "raw_path": str(raw_path),
            "adapted_path": str(adapted_path),
            "active_path": str(active_path)
        }

    def recruit_all_agents(self) -> List[Dict[str, Any]]:
        print("Recruiter & Chief Org Manager: Scanning and importing all core agents from repository...")
        recruited = []
        for agent_id in CORE_AGENT_ROSTER.keys():
            try:
                res = self.recruit_agent(agent_id)
                recruited.append(res)
                print(f"  ✓ Recruited: {res['title']} ({agent_id})")
            except Exception as e:
                print(f"  ✗ Failed {agent_id}: {e}")
        
        # Build organizational mesh and chart
        self.build_org_mesh()
        self.generate_org_chart()
        return recruited

    def build_org_mesh(self) -> Dict[str, Any]:
        mesh = {
            "title": "Strategist Autonomous Multi-Agent Organizational Mesh",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "recruiter_mode": "Zero Synthetic Generation - 100% Repository Sourced",
            "source_repo": "https://github.com/alirezarezvani/claude-skills",
            "total_agents": len(CORE_AGENT_ROSTER),
            "agents": {},
            "execution_loops": {
                "loop_1_discovery": {
                    "name": "Problem Discovery & Wait-Time Audit Loop",
                    "description": "Uncovers the ground-truth bottleneck, separates Value-Add from Wait and Rework time.",
                    "primary_agent": "cs-bizops-orchestrator",
                    "feedback_peers": ["cs-pm-orchestrator", "User"]
                },
                "loop_2_architecture": {
                    "name": "System Architecture & Workflow Topology Loop",
                    "description": "Translates ground-truth requirements into state-machine DAGs and system boundaries.",
                    "primary_agent": "cs-engineering-lead",
                    "feedback_peers": ["cs-workflow-architect", "cs-senior-engineer"]
                },
                "loop_3_tdd_adversarial": {
                    "name": "Loop A: TDD Adversarial Implementation Loop",
                    "description": "Test Architect writes adversarial tests first. Swarm engineers implement until 100% pass.",
                    "workers": ["cs-frontend-engineer", "cs-backend-engineer", "cs-fullstack-engineer"],
                    "adversaries": ["test-architect", "test-debugger"],
                    "circuit_breaker": "5 retries max before escalation"
                },
                "loop_4_code_quality": {
                    "name": "Adversarial Code Review & Patterns Loop",
                    "description": "Audits simplicity, readability, and resilience before promotion.",
                    "workers": ["cs-frontend-engineer", "cs-backend-engineer"],
                    "reviewers": ["karpathy-reviewer", "cs-senior-engineer"]
                },
                "loop_5_devops_infrastructure": {
                    "name": "Loop B: DevOps Runtime & Security Verification Loop",
                    "description": "Verifies container builds, static analysis, secrets, responsive viewports, and local health.",
                    "workers": ["cs-frontend-engineer", "cs-backend-engineer"],
                    "auditor": "devops-engineer"
                },
                "loop_6_governance_handoff": {
                    "name": "Governance, Swarm Coordination & Context Handoff",
                    "description": "Monitors token utilization, compacts memory state, and executes shift/turn handoffs.",
                    "governors": ["hub-coordinator", "cs-handoff-author", "Context Manager"]
                }
            }
        }

        for aid, meta in CORE_AGENT_ROSTER.items():
            mesh["agents"][aid] = {
                "title": meta["title"],
                "domain": meta["domain"],
                "loop": meta["loop"],
                "upstream": meta["upstream"],
                "downstream": meta["downstream"],
                "loop_peers": meta["loop_peers"],
                "installed": (RECRUITED_AGENTS_DIR / f"{aid}.md").exists()
            }

        mesh_file = STATE_DIR / "org_mesh.json"
        with open(mesh_file, "w", encoding="utf-8") as f:
            json.dump(mesh, f, indent=2)

        return mesh

    def generate_org_chart(self) -> str:
        chart_file = AGENTS_DIR / "ORGANIZATION_CHART.md"
        content = f"""# Strategist Multi-Agent Organizational Topology & Looping Mesh

> **Architect**: Recruiter & Chief Organizational Manager  
> **Source Canon**: [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills)  
> **Ingestion Policy**: Zero Synthetic Generation — 100% Real Imported Agents  

---

## 1. Executive Organization & Looping Topology

```mermaid
flowchart TD
    User([Business Stakeholder / User])

    subgraph Governance["Orchestration & Governance Level"]
        Recruiter["Recruiter & Chief Org Manager"]
        HubCoord["Hub Coordinator (AgentHub)"]
        ContextMgr["Context Manager & Handoff Author"]
    end

    subgraph Loop1["Loop 1: Discovery & Wait-Time Audit"]
        BizOps["BizOps Lead (cs-bizops-orchestrator)"]
        PM["PM Orchestrator (cs-pm-orchestrator)"]
        BizOps <-->|"Grill Discipline & Process Map"| PM
    end

    subgraph Loop2["Loop 2: System Architecture & Topology"]
        EngLead["Engineering Lead (cs-engineering-lead)"]
        WorkflowArch["Workflow Architect (cs-workflow-architect)"]
        EngLead <-->|"DAG & State Boundaries"| WorkflowArch
    end

    subgraph Loop3["Loop 3: TDD Adversarial Loop (Loop A)"]
        TestArch["Test Architect (test-architect)"]
        TestDbg["Test Debugger (test-debugger)"]
        
        subgraph DevSwarm["Engineering Swarm Workers"]
            FrontDev["Frontend Engineer (cs-frontend-engineer)"]
            BackDev["Backend Engineer (cs-backend-engineer)"]
            FullDev["Fullstack Engineer (cs-fullstack-engineer)"]
        end

        TestArch -->|"Adversarial Test Suite"| DevSwarm
        DevSwarm -->|"Implementation Artifacts"| TestDbg
        TestDbg -->|"Failure Diffs / Rejections"| DevSwarm
    end

    subgraph Loop4["Loop 4: Code Quality & Review"]
        Karpathy["Karpathy Code Reviewer"]
        SeniorEng["Senior Staff Engineer (cs-senior-engineer)"]
        DevSwarm <-->|"Code Cleanliness & Style"| Karpathy
        DevSwarm <-->|"Architectural Resilience"| SeniorEng
    end

    subgraph Loop5["Loop 5: DevOps & Infrastructure (Loop B)"]
        DevOps["DevOps Engineer (devops-engineer)"]
        DevSwarm -->|"Builds & Containers"| DevOps
        DevOps -->|"Remediation Reports"| DevSwarm
    end

    %% Flow connections
    User <-->|"Interrogation Gates"| BizOps
    BizOps -->|"00_PROBLEM_AUDIT.md"| PM
    PM -->|"02_GROUND_TRUTH_SRS.md"| EngLead
    EngLead -->|"03_TEST_ACCEPTANCE.md"| TestArch
    TestDbg -->|"100% Tests Pass"| Karpathy
    Karpathy -->|"Clean Code Certified"| DevOps
    DevOps -->|"Production Ready"| HubCoord
    HubCoord -->|"Continuous State Handoff"| ContextMgr
```

---

## 2. Recruited Roster & Operational Contracts

| Agent ID | Real Title | Domain | Loop Assignment | Looping Peers |
| :--- | :--- | :--- | :--- | :--- |
"""
        for aid, meta in CORE_AGENT_ROSTER.items():
            content += f"| `{aid}` | **{meta['title']}** | `{meta['domain']}` | {meta['loop']} | {', '.join(meta['loop_peers'])} |\n"

        content += """
---

## 3. Cyclic Looping & Convergence Protocols

1. **Depth-First Loop Closure**: No phase promotes linearly. Every milestone requires confirmation by an adversarial checker.
2. **Deterministic Precedence**: Test assertions outrank model opinions. Automated unit/integration tests must pass 100%.
3. **5-Iteration Circuit Breaker**: If any worker ⇄ checker loop exceeds 5 bounces without convergence, execution pauses and the Chief Org Manager escalates to the user with the consolidated audit log.
4. **Token Compaction Handoffs**: At 100k active tokens, the `cs-handoff-author` and `Context Manager` distill conversation state into immutable decisions before cycling agent threads.
"""
        chart_file.write_text(content, encoding="utf-8")
        return str(chart_file)


if __name__ == "__main__":
    rm = RecruiterManager()
    if "--all" in sys.argv or len(sys.argv) == 1:
        rm.recruit_all_agents()
    elif len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        rm.recruit_agent(sys.argv[1])
