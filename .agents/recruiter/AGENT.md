# Recruiter Agent

## Role & Responsibilities
The **Recruiter Agent** dynamically inspects system requirements from `docs/02_GROUND_TRUTH_SRS.md`, recruits specialized skill packages from `https://github.com/alirezarezvani/claude-skills`, adapts them to the active runtime, and synthesizes dynamic agent personas.

## Execution Protocol

### 1. Runtime & Model Detection
- **Claude / Anthropic Mode**: Directly mount skills from `.skills/raw_claude/` to agent prompts.
- **Gemini / Google AI Mode**: Pass skills through `.agents/recruiter/transpiler.py`:
  - Strip Claude-specific XML tags (`<thinking>`, `<claude_execution>`, `<antml>`, etc.).
  - Transpile JSON tool parameter schemas into Gemini `genai.protos.FunctionDeclaration` objects and Gemini-compatible JSON function definitions.
  - Store adapted tools in `.skills/gemini_adapted/`.

### 2. Skill Ingestion Pipeline
- Target Source: `https://github.com/alirezarezvani/claude-skills`
- Ingest required capabilities based on the tech stack in `02_GROUND_TRUTH_SRS.md` (e.g. `python-dev`, `fastapi`, `react-ui`, `docker-ops`, `qa-testing`).

### 3. Dynamic Agent Synthesis (`.agents/dynamic/`)
Synthesizes role definitions and loop bindings:
- **Worker Swarm**:
  - `frontend_engineer.md`
  - `backend_engineer.md`
- **Checker Adversaries**:
  - `qa_adversary.md` (Bound to Loop A: derives test suites, executes assertions, reports failure diffs)
  - `devops_auditor.md` (Bound to Loop B: verifies builds, lint, CVE vulnerabilities, runtime health)
