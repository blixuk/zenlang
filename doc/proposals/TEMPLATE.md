# RFC [Number]: [Feature / Proposal Title]

| Attribute | Value |
|:---|:---|
| **RFC Number** | [e.g. 0001] |
| **Title** | [Short, descriptive title] |
| **Author(s)** | [Author Name / Handle] |
| **Status** | Draft \| Under Review \| Accepted \| Rejected \| Deferred \| Implemented |
| **Created Date** | YYYY-MM-DD |
| **Target Specification** | [doc/SPECIFICATION.md](../SPECIFICATION.md) |
| **Documentation Standards** | [doc/DOCUMENTATION_STANDARDS.md](../DOCUMENTATION_STANDARDS.md) |

---

## 1. Summary & Abstract
A concise 1-2 paragraph executive summary explaining what syntax or feature is being proposed.

---

## 2. Motivation & Value to Zenlang
- **Problem Statement:** What problem or limitation currently exists in Zenlang that necessitates this change?
- **Why Zenlang Needs This:** How does this feature benefit developers, scripts, terminal apps, or services?
- **Alignment with Zen Manifesto:** How does this proposal adhere to the core principles (simplicity, visual flow, explicitness over magic, Unix-first)?

---

## 3. Detailed Syntax & Semantics

### 3.1 Proposed Syntax
Provide exact grammar rules and code examples using the `zl` code block format:

```zl
// Example of the proposed syntax in action
```

### 3.2 Semantic Rules & Precedence
- Detailed evaluation rules.
- Operator precedence and associativity (if introducing operators).
- Scope boundaries and variable lifetime.

---

## 4. Impact on Three-Layer Architecture

Every proposal must evaluate its impact across all three execution layers:

| Layer | Impact & Implementation Requirements |
|:---|:---|
| **1. Universal `ZenValue` ABI** | Does this require new `ZenValue` tag types or runtime C helpers? |
| **2. Compiler Positional IR** | What new AST node kinds are required in `AST.zl`? |
| **3. Execution Engine** | What changes are needed in `Bytecode.zl` (VM opcodes) and `Codegen.zl` (C transpilation)? |

---

## 5. Standard Library & Tooling Impact
- Does this impact existing `lib/zen/` packages?
- Does this affect the Formatter (`zenfmt`), DocGen (`zendoc`), LSP (`zenlsp`), or REPL (`zen repl`)?

---

## 6. Drawbacks & Alternatives Considered
- **Drawbacks / Costs:** What complexity or runtime overhead does this introduce?
- **Library Alternative:** Why can't this be implemented as a standard library function instead of core syntax?
- **Alternative Syntaxes:** What alternative syntax forms were considered and why were they rejected?

---

## 7. Edge Cases & Verification Plan
- Specific edge cases to test.
- Plan for compiler unit tests and parity test fixtures.

---

## 8. Unresolved Questions
Any open design questions that require discussion during the review period.
