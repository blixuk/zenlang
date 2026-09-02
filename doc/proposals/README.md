# Zenlang Feature Proposals & RFC Process

| Attribute | Value |
|:---|:---|
| **Role** | Language Evolution & Proposal Governance |
| **Authority** | Formal Review Gateway for Syntax & Semantic Changes |
| **Specification Reference** | [doc/SPECIFICATION.md](../SPECIFICATION.md) |
| **Documentation Standards** | [doc/DOCUMENTATION_STANDARDS.md](../DOCUMENTATION_STANDARDS.md) |

---

## 1. Overview & Purpose

To preserve Zenlang's core principles—**simplicity over cleverness, explicitness over magic, and consistency across the Three-Layer Architecture**—all proposed syntax modifications, language operators, new keywords, or core semantic changes must undergo a formal **Request for Comments (RFC)** process.

No feature or syntax addition may be added to [doc/SPECIFICATION.md](../SPECIFICATION.md) or implemented in the compiler without completing this lifecycle.

---

## 2. Proposal Lifecycle

Every proposal progresses through structured phases:

```
┌─────────────┐     ┌─────────────────────┐     ┌──────────────────────┐
│  1. DRAFT   │ ──> │ 2. REVIEW & DEBATE  │ ──> │ 3. DECISION          │
│ (TEMPLATE)  │     │ (Evaluate against   │     │ (Accepted, Rejected, │
└─────────────┘     │  Zen Manifesto)     │     │  or Deferred)        │
                    └─────────────────────┘     └──────────┬───────────┘
                                                           │
                                                           ▼ (If Accepted)
┌──────────────────────┐     ┌──────────────────────┐      │
│ 5. CANONIZATION      │ <── │ 4. IMPLEMENTATION    │ <────┘
│ (Merged to SPEC.md)  │     │ (Compiler + Tests)   │
└──────────────────────┘     └──────────────────────┘
```

### Stages:
1. **Draft:** The proposal author copies [`TEMPLATE.md`](TEMPLATE.md) into a new RFC file (e.g. `0001_pattern_guard_syntax.md`) with a complete technical design.
2. **Review & Evaluation:** The proposal is reviewed against the [Zen Manifesto](../Zen%20Manifesto.md):
   - *Does it add unnecessary syntactic complexity?*
   - *Can it be achieved with existing stdlib libraries or patterns instead?*
   - *What is the impact on the Three-Layer Architecture (`ZenValue` ABI, Bytecode VM, Positional IR, and C AOT)?*
3. **Decision:**
   - **Accepted:** The proposal is approved for implementation.
   - **Rejected:** The proposal does not fit Zenlang's design goals (rationale recorded).
   - **Deferred:** Placed on hold pending prerequisite features.
4. **Implementation:** Implemented in `selfhost/compiler/` and verified across `./scripts/zen test` / `ci-soak`.
5. **Canonization:** The new syntax and semantics are merged into [doc/SPECIFICATION.md](../SPECIFICATION.md).

---

## 3. Creating a New Proposal

To author an RFC:
1. Copy `TEMPLATE.md` to `doc/proposals/XXXX-descriptive-title.md` (where `XXXX` is the next sequential proposal number).
2. Fill out all sections thoroughly.
3. Submit for review.

---

## 4. Proposal Index

| RFC Number | Title | Status | Date | Primary Author |
|:---|:---|:---|:---|:---|
| — | *No active RFCs under review* | — | — | — |
