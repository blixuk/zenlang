Here is a mock program that acts as a **Log Analyzer**. It demonstrates ZenLang’s commitment to the Unix philosophy by utilizing the native process piping system to filter a file *before* bringing the data into ZenLang’s memory, where it is then parsed using the standard library's `logfmt`.

This script grabs the last 5 error logs from a server log file and formats them into a clean report.

```zenlang
// --- log_analyzer.zs ---

// 1. Imports
from zen.io import out
from formats import logformat as logfmt
import process

// 2. Named Scope for Configuration
scope Config {
    set LOG_FILE : String -> `/var/log/server.log`
    set TARGET_LEVEL : String -> `error`
    set MAX_RESULTS : Integer -> 5
}

// 3. Task for Log Processing
task analyze_logs : Void {
    out.info(f`Starting analysis of {Config.LOG_FILE}...`)

    // 4. Native Process Piping
    // We delegate the heavy lifting to the OS, streaming the file through grep and tail.
    let pipeline -> process.spawn(f`cat {Config.LOG_FILE}`)
        .pipe(f`grep level={Config.TARGET_LEVEL}`)
        .pipe(f`tail -n {Config.MAX_RESULTS}`)
        
    // 5. Error Check Operator (?)
    // If the pipeline fails (e.g., file not found), we catch the Error variant, 
    // log it, and early-return 'Default' (Void).
    let raw_output : String -> ? pipeline.run() or {
        out.error(`Failed to read or filter logs. Does the file exist?`)
        <- Default 
    }

    // Early exit if the string is empty
    when raw_output == `` {
        out.info(`No errors found today!`)
        <- Default
    }

    out.write(`\n--- Recent Server Errors ---`)

    // 6. Text Processing
    // Split the raw string by newline to get a List of Strings
    let lines : List<String> -> raw_output.split(`\n`)

    // 7. Iteration
    do for line in lines {
        // Skip empty trailing lines
        when line == `` { continue }

        // 8. "Dumb but Honest" Data Format Parsing
        // logfmt parses "time=10:00 level=error msg=timeout" into a Map
        let entry : Map<String, String> -> logfmt.parse(line)
        
        let timestamp -> entry[`time`]
        let message   -> entry[`msg`]
        
        // Inline conditional to provide a fallback if the 'user' key is missing
        let user -> entry[`user`] when entry[`user`] != Default or `System`

        // 9. Structured Output
        out.write(f`[{timestamp}] User '{user}': {message}`)
    }
    
    out.write(`--- End of Report ---\n`)
}

// Main execution
function main {
    // Suspend the main task until the analyzer finishes
    analyze_logs().wait
}
```

### Key Takeaways from this Mockup:

* **The `process.pipe` chain:** Notice how we don't have to write a custom loop in ZenLang to read the file chunk by chunk just to search for the word "error". By using `process.spawn("...").pipe("...").run()`, ZenLang safely wraps standard Unix utilities, treating them as first-class citizens.
* **The `? ... or { ... }` block:** This is where ZenLang's error handling shines. `pipeline.run()` returns a `[String, Error]` union. The `?` operator attempts to unwrap the `String`. If it hits an `Error`, it immediately falls back to the `or` block, logging the failure and safely exiting the task (`<- Default`).
* **Built-in `logfmt`:** By including parsers like `logfmt` and `columns` (CSV) in the core library, ZenLang prevents developers from having to write brittle regex just to extract data from standard formats.