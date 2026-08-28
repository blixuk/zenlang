# Purpose

The Zenlang Asynchronous workflows and Promises subsystem. Provides monadic Promises, Deferred objects, parallel/series orchestrators, retry loops with backoff, condition polling, and delay timers.

# Ownership

Standard library maintainers.

# Local Contracts

- **Promises / Futures (`future.zl`)**: State machine (`PENDING`, `FULFILLED`, `REJECTED`) with `then`, `catch`, settlement inspection, and decoupled `Deferred` objects.
- **Async Combinators (`async.zl`)**: High-level workflow orchestration functions: `parallel` fan-out, `series` sequencing, `retry` with backoff, and condition `poll`.
- **Dual-Path Execution**: Fully compliant with AST interpreter and native C AOT compiler (`-g`).

# Work Guidance

- Prefer `zen.async` canonical imports (`zen.async.future`, `zen.async.async`).
- Keep async combinators pure and non-destructive.

# Verification

- Automated test suite: `tests/lib/test_concurrency.zl`

# Child DOX Index

- future.zl: Promise state machine, then/catch callbacks, settlement checks, and Deferred factories
- async.zl: Parallel, series, retry, poll, and delay workflow combinators
