# 03: Test Acceptance Criteria & Definition of Done

> **Author**: QA Adversary & System Orchestrator  
> **Status**: Pending Dynamic Recruitment  
> **Project**: Strategist  

---

## 1. Adversarial Test Acceptance Matrix (Loop A Gating)
*The QA Adversary writes unit and integration tests based on these criteria BEFORE workers write production code.*

| Test ID | Target Component | Input / Precondition | Adversarial Scenario / Edge Case | Expected Assertion | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TEST-001` | *Ingress Parser* | *Malformed payload* | *Missing required field & SQL injection attempt* | *HTTP 422 + Clean error schema* | `PENDING` |
| `TEST-002` | *Core Workflow* | *Concurrent requests* | *Race condition on inventory decrement* | *Atomic consistency, 0 oversell* | `PENDING` |

---

## 2. Runtime, Infrastructure & Security Criteria (Loop B Gating)
- [ ] **Lint & Static Analysis**: Zero lint errors, zero unused imports, strict typing enabled.
- [ ] **Dependency Security Audit**: Zero high/critical CVEs in packages.
- [ ] **Build & Packaging**: Clean reproducible build (`npm run build`, `pytest`, `docker build`).
- [ ] **Secrets & Config Audit**: No API keys or credentials checked into repo; `.env.example` verified.

---

## 3. Definition of Done (DoD)
1. 100% of Loop A adversarial tests passing.
2. 100% of Loop B runtime/security checks verified by DevOps Auditor.
3. No unresolved items in `.state/loop_audit.json`.
4. User sign-off on delivered milestone.
