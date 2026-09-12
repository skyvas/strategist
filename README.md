# Strategist: Business-First Autonomous Multi-Agent Ecosystem

An autonomous multi-agent development engine that interrogates the business problem to reach ground truth, dynamically recruits and adapts skill packages, and enforces cyclic feedback loops (`Swarm ⇄ QA ⇄ DevOps`) to build and verify software solutions.

## Architecture

```
.
├── .agents/                    # Agent persona prompts & runtime specs
│   ├── business_analyst/       # BA interrogation and requirements prompts
│   ├── recruiter/              # Chief Org Manager, Talent Recruiter & Looping Architect
│   ├── context_manager/        # Token monitoring & state serialization logic
│   ├── recruited/              # 100% Repository-sourced real agents from claude-skills
│   └── ORGANIZATION_CHART.md   # Complete multi-agent organizational mesh & loop chart
├── .skills/                    # Skill definitions and toolsets
│   ├── raw_claude/             # Cloned/downloaded skills from GitHub
│   └── gemini_adapted/         # Transpiled Gemini-compatible tool schemas
├── .state/                     # Context memory & persistent checkpoints
│   ├── memory_graph.json       # Graph of business rules, decisions, and constraints
│   ├── session_state.json      # Current execution checkpoint and active agents
│   ├── loop_audit.json         # Iteration counters, regression logs, and bounce histories
│   └── org_mesh.json           # Active agent contracts and interlocking execution loops
├── docs/                       # Ground truth specifications
│   ├── 00_PROBLEM_AUDIT.md     # Raw business challenge breakdown
│   ├── 01_ECOSYSTEM_TOPOLOGY.md# High-level architecture (Single app vs multi-app)
│   ├── 02_GROUND_TRUTH_SRS.md  # Software Requirements Specification
│   └── 03_TEST_ACCEPTANCE.md   # Definition of Done and QA verification criteria
├── src/                        # Implementation workspaces (sub-folders for multi-apps)
└── strategist.py               # Master orchestrator CLI
```

## CLI Usage

```bash
# Check status, token limits, and loop health
python3 strategist.py status

# Display organizational mesh & cyclic feedback loops
python3 strategist.py mesh

# Recruit/synchronize all core agents from claude-skills
python3 strategist.py recruit --all

# Run transpiler self-test
python3 strategist.py transpile-test

# Compact context state
python3 strategist.py compact --summary "Phase 1 complete"
```
