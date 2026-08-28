= Terminal Mastery & UI

Zenlang treats the terminal as a primary graphical and interactive surface. In this chapter, you will learn how to build rich, zero-flicker terminal interfaces and CLI tools.

== Terminal Control (`zen.sys.term`)

The `zen.sys.term` package gives you low-level, high-speed control over the terminal:

```zl
use zen.sys.term as term

function main() {
    term.alt_screen_enter() // Switch to clean alternate buffer
    term.raw_enter()        // Receive key events immediately
    term.clear()

    term.move(10, 5)        // Move cursor to (col 10, row 5)
    term.color(`green`, `black`)
    term.write(`Welcome to Zenlang TUI!`)

    let key -> term.read_key() // Wait for any key press

    term.raw_exit()
    term.alt_screen_exit()
    <- 0
}
```

== Declarative Tables (`zen.ui.table`)

Formatting tabular data is effortless with `zen.ui.table`:

```zl
use zen.io
use zen.ui.table as table

function main() {
    let headers -> [`Process`, `CPU %`, `RAM (MB)`, `Status`]
    let rows -> [
        [`zen_compiler`, `12.5`, `45.2`, `Running`],
        [`postgres`,      `4.1`, `210.0`, `Active`],
        [`web_server`,    `0.8`,  `32.4`, `Idle`]
    ]

    // Render with rounded Unicode borders
    let output -> table.format_table(headers, rows, { `style` -> `rounded` })
    io.writeln(output)
    <- 0
}
```

== Animated Spinners (`zen.ui.spinner`)

To give users feedback during background tasks:

```zl
use zen.ui.spinner as spinner
use zen.sys.term as term

function main() {
    let s -> spinner.create(`Compiling project...`, `dots`)

    let step -> 0
    do while step < 20 {
        s.tick()
        term.poll_key(100) // Sleep 100ms
        step -> 0 + step + 1
    }

    s.success(`Build completed in 2.0s!`)
    <- 0
}
```

== Visual Charts & Sparklines (`zen.ui.chart`)

Render real-time telemetry and metrics:

```zl
use zen.io
use zen.ui.chart as chart

function main() {
    let telemetry -> [10, 25, 45, 80, 95, 70, 40, 60, 85, 100]
    let spark -> chart.sparkline(telemetry)

    io.writeln(`Network Traffic: ` + spark)
    // Prints: Network Traffic:  ▂▄▆█▆▃▅▇█
    <- 0
}
```
