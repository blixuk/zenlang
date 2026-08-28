# Chapter 11: Practical Projects

In this final chapter, we will synthesize everything we have learned into two complete, practical applications.

---

## 1. Project 1: Unix Log Analyzer (`zlog.zl`)

A high-speed CLI tool that parses server log files, counts HTTP status codes, and outputs a formatted table with a visual frequency distribution:

```zenlang
// zlog.zl
use zen.io
use zen.io.file as file
use zen.sys.sys as sys
use zen.text.string as Str
use zen.ui.table as table

function main() {
    let args -> sys.get_args()
    when args.length < 2 {
        io.writeln(`Usage: zlog <logfile.log>`)
        <- 1
    }

    let filepath -> args[1]
    when not file.exists(filepath) {
        io.writeln(`File not found: ` + filepath)
        <- 1
    }

    let lines -> file.read_lines(filepath)
    let counts -> { `200` -> 0, `404` -> 0, `500` -> 0, `other` -> 0 }

    let i -> 0
    do while i < lines.length {
        let line -> lines[i]
        when Str.contains(line, ` 200 `) {
            counts[`200`] -> counts[`200`] + 1
        } or when Str.contains(line, ` 404 `) {
            counts[`404`] -> counts[`404`] + 1
        } or when Str.contains(line, ` 500 `) {
            counts[`500`] -> counts[`500`] + 1
        } or {
            counts[`other`] -> counts[`other`] + 1
        }
        i -> 0 + i + 1
    }

    let headers -> [`Status Code`, `Count`, `Description`]
    let rows -> [
        [`200 OK`, Str.to_string(counts[`200`]), `Successful HTTP requests`],
        [`404 Not Found`, Str.to_string(counts[`404`]), `Missing resource requests`],
        [`500 Server Error`, Str.to_string(counts[`500`]), `Internal server errors`],
        [`Other`, Str.to_string(counts[`other`]), `Redirects / Other`]
    ]

    io.writeln(`\n--- ACCESS LOG ANALYSIS: ` + filepath + ` ---`)
    io.writeln(table.format_table(headers, rows, { `style` -> `rounded` }))
    <- 0
}
```

---

## 2. Project 2: Interactive Terminal Task Manager (`ztodo.zl`)

A split-screen interactive task list with live keyboard navigation:

```zenlang
// ztodo.zl
use zen.io
use zen.sys.term as term
use zen.text.string as Str

class TodoApp {
    let tasks -> [
        { `title` -> `Write Zenlang book chapters`, `done` -> True },
        { `title` -> `Test dual-path native compilation`, `done` -> True },
        { `title` -> `Ship 1.0 release`, `done` -> False }
    ]
    let selected -> 0
    let running -> True

    function draw() {
        term.move(1, 1)
        term.write(`\033[30;102m 📋 ZEN TODO MANAGER — [Space:Toggle  ↑/↓:Nav  Q:Quit] \033[0m\n\n`)

        let i -> 0
        do while i < self.tasks.length {
            let task -> self.tasks[i]
            let prefix -> `  `
            when i == self.selected { prefix -> `▶ ` }

            let checkmark -> `[ ] `
            when task.done { checkmark -> `[✔] ` }

            when i == self.selected {
                term.write(`\033[36m` + prefix + checkmark + task.title + `\033[0m\n`)
            } or {
                term.write(prefix + checkmark + task.title + `\n`)
            }
            i -> 0 + i + 1
        }
    }

    function run() {
        term.alt_screen_enter()
        term.raw_enter()
        term.clear()

        do while self.running {
            self.draw()
            let key -> term.read_key()
            when key.name == `up` or key.ch == `k` {
                when self.selected > 0 { self.selected -> self.selected - 1 }
            } or when key.name == `down` or key.ch == `j` {
                when self.selected < self.tasks.length - 1 { self.selected -> self.selected + 1 }
            } or when key.ch == ` ` {
                self.tasks[self.selected].done -> not self.tasks[self.selected].done
            } or when key.ch == `q` or key.ch == `Q` {
                self.running -> False
            }
        }

        term.raw_exit()
        term.alt_screen_exit()
    }
}

function main() {
    let app -> TodoApp()
    app.run()
    <- 0
}
```

---

## 🚀 What Next?

Congratulations on completing *The Zen of Programming*! You now possess a deep understanding of Zenlang's syntax, visual data flow, type system, standard library, and dual execution model.

To continue your journey:
- Explore the **[Standard Library Reference](../Standard_Library_Reference.md)**
- Check out the **[Language Specification](../Specification/Zenlang.pdf)**
- Join the community and build high-performance terminal tools!
