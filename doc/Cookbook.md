# Zenlang Cookbook & Integration Patterns

Practical, executable recipes for building CLI utilities, terminal user interfaces, data processing pipelines, and high-performance native integrations in Zenlang.

---

## Recipe 1: Building a Unix CLI Utility with Arguments & Colors

```zen
import zen.sys.sys as sys
import zen.sys.cli as cli
import zen.color.color as color
import zen.io.io as io
import zen.text.string as Str

function main() {
    let args -> sys.get_args()
    
    when args.length < 2 {
        let warn -> color.format(`[USAGE] mycli <input_file> [--verbose]`, color.YELLOW, Default)
        io.writeln(warn)
        <- 1
    }
    
    let filename -> args[1]
    let verbose  -> args.has(`--verbose`)
    
    when verbose == True {
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

```zen
import zen.ui.canvas as canvas
import zen.sys.term as term
import zen.sys.term_keys as keys
import zen.time.time as time

function main() {
    let cv -> canvas.create(80, 24)
    let x -> 10
    let y -> 10
    let running -> True
    
    term.enable_raw_mode()
    term.hide_cursor()
    
    do while running == True {
        canvas.clear(cv)
        canvas.draw_box(cv, 0, 0, 79, 23, `solid`)
        canvas.draw_text(cv, x, y, `* Zenlang TUI *`)
        canvas.render(cv)
        
        let key -> keys.poll_key(16) // 60 FPS poll
        when key == `q` or key == `ESCAPE` {
            set running -> False
        } or when key == `UP` and y > 1 {
            set y -> y - 1
        } or when key == `DOWN` and y < 22 {
            set y -> y + 1
        } or when key == `LEFT` and x > 1 {
            set x -> x - 1
        } or when key == `RIGHT` and x < 60 {
            set x -> x + 1
        }
    }
    
    term.show_cursor()
    term.disable_raw_mode()
    <- 0
}
```

---

## Recipe 3: High-Performance JSON & Zen Data Serialization

```zen
import zen.data.json as json
import zen.data.zendata as zd
import zen.io.file as file
import zen.io.io as io

function convert_json_to_zendata(input_path, output_path) {
    check {
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
}
```

---

## Recipe 4: Batch Memory Processing with Scoped Arenas

```zen
import zen.memory as memory
import zen.io.io as io
import zen.text.string as Str

function process_large_stream(stream_chunks) {
    // Allocate 32MB bump arena for processing this stream
    with memory.create_arena(32 * 1024 * 1024) as arena {
        let total_bytes -> 0
        do for chunk in stream_chunks {
            let upper -> Str.to_upper(chunk)
            set total_bytes -> total_bytes + Str.length(upper)
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
```zen
import zen.reflect as reflect

function main() {
    let engine -> reflect.load_module(`./libengine.so`)
    let result -> reflect.call(engine, `compute_mesh`, [1000, 2000])
    io.writeln(`Calculated mesh: ` + Str.to_string(result))
    <- 0
}
```
