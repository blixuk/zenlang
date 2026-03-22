The ZenLang Manifesto
1. Purpose

ZenLang exists to be a modern Unix-native programming language for building scripts, terminal applications, and networked services using a single coherent model.

ZenLang is designed for developers who value:

Simplicity over cleverness

Composition over frameworks

Explicitness over magic

Tools that work with Unix, not against it

ZenLang is not intended to replace Unix.
ZenLang is intended to extend Unix.

2. Core Philosophy
2.1 ZenLang follows the Unix philosophy

ZenLang embraces the foundational Unix ideas:

Do one thing well

Compose programs through well-defined interfaces

Prefer text and streams as universal data formats

Make tools scriptable

Keep the core small; grow power through libraries

ZenLang programs should be easy to connect, pipe, embed, and automate.

2.2 ZenLang is terminal-first

The terminal is not a legacy interface.
It is a primary execution environment.

ZenLang treats the terminal as:

A structured output surface

A stateful input device

A real-time UI target

Terminal applications are not “second-class” compared to web or GUI applications.

2.3 ZenLang is compiled and interpreted

ZenLang supports:

Interactive interpretation

Bytecode execution on a virtual machine

Ahead-of-time native compilation

All execution modes share:

The same syntax

The same semantics

The same standard library

There is no “scripting subset” and no “compiled-only features”.

3. Language Design Principles
3.1 Explicit over implicit

ZenLang avoids:

Hidden control flow

Implicit type coercions

Context-dependent behavior

What a program does should be obvious from reading it.

3.2 Simple core, powerful libraries

The language core is intentionally small:

Minimal keywords

Minimal syntax

Clear semantics

Power is delivered through:

Standard libraries

First-class modules

Well-defined abstractions

ZenLang resists language bloat.

3.3 Practical typing

ZenLang supports optional static typing.

Typing exists to:

Improve correctness

Improve tooling

Improve documentation

Typing must never prevent rapid scripting or exploration.

3.4 Structured concurrency

ZenLang favors structured concurrency over ad-hoc threading.

Concurrency should be:

Explicit

Scoped

Predictable

ZenLang avoids shared mutable state by default and provides clear async semantics.

4. Streams and Composition
4.1 Streams are first-class

ZenLang treats:

stdin

stdout

stderr

files

sockets

processes

as streams with shared semantics.

Pipelines are language constructs, not shell hacks.

4.2 Programs are components

A ZenLang program should:

Be callable from the shell

Be embeddable in scripts

Be usable as a library

Be composable with other programs

ZenLang blurs the line between “tool” and “library”.

5. Terminal and UI Philosophy
5.1 Terminal UI is a real UI

ZenLang provides:

Structured terminal rendering

Input handling

Layout systems

Styling abstractions

Applications should not manually emit escape codes unless explicitly required.

5.2 Unified UI model

ZenLang defines a single declarative UI model that can be rendered to:

Terminal (TUI)

HTML (Web)

The same application logic should run:

Locally in a terminal

Remotely in a browser

Rendering is a backend detail.

6. Web Philosophy
6.1 ZenLang is full-stack capable

ZenLang supports:

HTTP servers

Routing

Middleware

Templating

WebSockets

Web development should not require switching languages or mental models.

6.2 Minimal JavaScript dependency

ZenLang does not depend on JavaScript by default.

Client-side behavior may be handled by:

Server-side rendering

WebSocket-driven updates

Optional WASM targets

JavaScript is an interoperability option, not a requirement.

7. Data and Persistence
7.1 Embedded-first data storage

ZenLang favors embedded databases for:

Simplicity

Portability

Scriptability

Key-value stores, document stores, and query systems are part of the standard ecosystem.

External databases are supported via adapters, not assumptions.

8. System Integration
8.1 Unix is the platform

ZenLang embraces:

POSIX processes

Signals

Filesystems

Permissions

Environment variables

ZenLang does not attempt to abstract Unix away.

8.2 Bash is not the enemy

ZenLang does not replace the shell.

ZenLang:

Coexists with Bash

Integrates with shell workflows

Improves scripting where Bash becomes brittle

9. Tooling and Ecosystem
9.1 First-class tooling

ZenLang tooling is part of the ecosystem:

Formatter

Linter

Package manager

REPL

Compiler

Tooling must be predictable, scriptable, and composable.

9.2 Small, understandable packages

ZenLang favors:

Few dependencies

Clear versioning

Transparent builds

The ecosystem prioritizes clarity over scale.

10. Long-Term Vision

ZenLang aims to be:

A serious systems scripting language

A powerful terminal application platform

A pragmatic web development tool

A stable foundation for Unix-based workflows

ZenLang rejects:

Trend-driven design

Excessive abstraction

Framework lock-in

ZenLang values:

Longevity

Simplicity

Composability

Developer control

11. Closing Principle

ZenLang exists to help developers build useful things simply, using tools that respect both the machine and the human.

ZenLang is calm.
ZenLang is deliberate.
ZenLang is Unix.