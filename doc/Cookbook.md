# Zenlang Cookbook & Integration Patterns

| Attribute | Value |
|:---|:---|
| **Role** | Practical Recipe & Pattern Cookbook |
| **Authority** | Derived Guides & Examples |
| **Specification Reference** | [doc/SPECIFICATION.md](SPECIFICATION.md) |
| **Documentation Standards** | [doc/DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) |

---

## 1. Overview

Practical, executable recipes for building CLI utilities, terminal user interfaces, data processing pipelines, and high-performance native integrations in Zenlang.

---

## Recipe 1: Building a Unix CLI Utility with Arguments & Colors

```zl
use zen.sys.sys as sys
use zen.color.color as color
use zen.io
use zen.text.string as Str

function main() {
    let args -> sys.get_args()
    
    when args.length < 2 {
        let warn -> color.format(`[USAGE] mycli <input_file> [--verbose]`, color.YELLOW, Default)
        io.writeln(warn)
        <- 1
    }
    
    let filename -> args[1]
    let verbose  -> args.has(`--verbose`)
    
    when verbose {
        let msg -> color.format(`Processing file: ` + filename, color.CYAN, Default)
        io.writeln(msg)
    }
    
    let success -> color.format(`Success! Processed ` + filename, color.GREEN, Default)
    io.writeln(success)
    <- 0
}
```

---

## Recipe 2: Interactive 60 FPS Terminal Animation / Canvas

```zl
use zen.ui.canvas as canvas
use zen.sys.term as term
use zen.sys.term_keys as keys
use zen.time.time as time

function main() {
    let cv -> canvas.create(80, 24)
    let x -> 10
    let y -> 10
    let running -> True
    
    term.enable_raw_mode()
    term.hide_cursor()
    
    do while running {
        canvas.clear(cv)
        canvas.draw_box(cv, 0, 0, 79, 23, `solid`)
        canvas.draw_text(cv, x, y, `* Zenlang TUI *`)
        canvas.render(cv)
        
        let key -> keys.poll_key(16) // 60 FPS poll
        when key == `q` or key == `ESCAPE` {
            running -> False
        } or when key == `UP` and y > 1 {
            y -> y - 1
        } or when key == `DOWN` and y < 22 {
            y -> y + 1
        } or when key == `LEFT` and x > 1 {
            x -> x - 1
        } or when key == `RIGHT` and x < 60 {
            x -> x + 1
        }
    }
    
    term.show_cursor()
    term.disable_raw_mode()
    <- 0
}
```

---

## Recipe 3: High-Performance JSON & Zen Data Serialization

```zl
use zen.data.json as json
use zen.data.zendata as zd
use zen.io.file as file
use zen.io

function convert_json_to_zendata(input_path: String, output_path: String) {
    let result -> check {
        let raw_json -> file.read(input_path)
        let parsed_data -> json.parse(raw_json)
        
        // Convert to human-readable Zen Data (.zd)
        let zdata_str -> zd.stringify(parsed_data)
        file.write(output_path, zdata_str)
        
        io.writeln(`Successfully converted ` + input_path + ` -> ` + output_path)
        <- { `ok` -> True }
    } or {
        <- { `ok` -> False, `error` -> `Failed to process JSON file` }
    }
    <- result
}
```

---

## Recipe 4: Batch Memory Processing with Scoped Arenas

```zl
use zen.memory as memory
use zen.io
use zen.text.string as Str

function process_large_stream(stream_chunks) {
    // Allocate 32MB bump arena for processing this stream
    with memory.create_arena(32 * 1024 * 1024) as arena {
        let total_bytes -> 0
        do for chunk in stream_chunks {
            let upper -> Str.to_upper(chunk)
            total_bytes -> total_bytes + Str.length(upper)
        }
        io.writeln(`Processed ` + Str.to_string(total_bytes) + ` bytes in arena.`)
    }
    // Entire 32MB arena is freed instantly in O(1)
}
```

---

## Recipe 5: Mixed ABI Execution (Interpreted Script Calling Native Module)

Compile the performance-critical engine module to native C:
```bash
zen compile src/engine.zl output/engine.c
gcc output/engine.c -shared -fPIC -I runtime/ -o libengine.so
```

Import and call it dynamically from an interpreted script:
```zl
use zen.reflect as reflect
use zen.io
use zen.text.string as Str

function main() {
    let engine -> reflect.load_module(`./libengine.so`)
    let result -> reflect.call(engine, `compute_mesh`, [1000, 2000])
    io.writeln(`Calculated mesh: ` + Str.to_string(result))
    <- 0
}
```

---

## Recipe 6: Concurrent Worker Pipeline with Channels & Tasks

```zl
use zen.io
use zen.text.string as Str

task worker(id: Integer, in_ch, out_ch) {
    let job -> in_ch.receive
    let processed -> `Worker ` + Str.to_string(id) + ` finished ` + job
    out_ch.send(processed)
}

function main() {
    let in_ch  -> channel(String)
    let out_ch -> channel(String)

    // Spawn 3 concurrent workers:
    with task_group as group {
        worker(1, in_ch, out_ch).spawn
        worker(2, in_ch, out_ch).spawn
        worker(3, in_ch, out_ch).spawn

        in_ch.send(`Job Alpha`)
        in_ch.send(`Job Beta`)
        in_ch.send(`Job Gamma`)

        do for i in 1...3 {
            let res -> out_ch.receive
            io.writeln(res)
        }
    }
    <- 0
}
```

---

## Recipe 7: Robust Error Handling with `check`, `raise` & `assert`

```zl
use zen.io
use zen.io.file as file

function load_secure_config(path: String) : [Map, Error] {
    // 1. Invariant assertion:
    assert path.length > 0 raise `InvalidPathError`

    // 2. Validate existence:
    when not file.exists(path) {
        ^ `FileNotFoundError` with path
    }

    let content -> file.read_all(path)
    <- { `config` -> content }
}

function main() {
    // Recover gracefully with fallback:
    let cfg -> check load_secure_config(`app.zd`) or {
        io.warn(`Config missing, falling back to defaults`)
        <- { `config` -> `default_mode -> True` }
    }

    io.info(`Active config: ` + cfg[`config`])
    <- 0
}
```

