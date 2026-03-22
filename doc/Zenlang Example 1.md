Here is a simple mock program written in ZenLang. It is a **CLI Weather Tool** that asks the user for a city, simulates fetching data asynchronously, handles potential errors, and formats the output.

This script demonstrates ZenLang's core features in action: explicit scopes, visual data flow (`->`, `<-`), task-based concurrency without `await` clutter, explicit time primitives, and the `out` stream replacing `print`.

```zenlang
// --- weather_cli.zs ---

// 1. Imports
from zen.io import out, in
import time

// 2. Named Scope for Configuration
scope Config {
    set APP_NAME : String -> `ZenWeather CLI`
    set DEFAULT_CITY : String -> `London`
}

// 3. Lightweight Value Type
structure WeatherData {
    city      : String
    temp      : Decimal
    condition : String
}

// 4. Task with Error Union Return Type
// Simulates an async network call that might fail
task fetch_weather(city: String) : [WeatherData, Error] {
    out.debug(f`Connecting to weather service for {city}...`)
    
    // Using first-class time primitives to suspend the task
    time.sleep(500.ms) 
    
    // Unified conditional to simulate a missing city
    when city == `Atlantis` {
        ^ `CityNotFoundError`  // ^ Immediately raises the error variant
    }
    
    // <- Visual return of a populated Structure
    <- WeatherData(
        city -> city,
        temp -> 22.5,
        condition -> `Sunny`
    )
}

// 5. Main Execution Function
function main {
    out.info(`Starting {Config.APP_NAME}...`)
    out.write(`Enter a city name (or press Enter for default):`)
    
    // Read input stream
    let input : String -> in.read.line()
    
    // Inline conditional (Ternary equivalent)
    let target_city -> Config.DEFAULT_CITY when input == `` or input
    
    // 6. Error Handling & Task Waiting
    // Suspend until fetch_weather completes, and handle the union type
    let result -> check fetch_weather(target_city).wait {
        case is Error {
            out.error(f`Failed to fetch data: {result}`)
            <- Default // Exit the check block gracefully
        }
        case is WeatherData {
            <- result
        }
    }
    
    // 7. Final Output Stream
    when result != Default {
        // Using explicit formatting directly into the output stream
        out.write(
            f`\nWeather Report for {result.city}:`
        )
        out.write(
            f`Temperature: {result.temp}°C | Condition: {result.condition}`
        )
    }
    
    out.write(`\nGoodbye!`)
}
```

### Why this feels like ZenLang:
1. **Readable Assignments:** The `->` and `<-` arrows make it incredibly easy to scan the code and see exactly where data is coming from and where it is going.
2. **No `async/await` Boilerplate:** Notice `fetch_weather(target_city).wait`. The function itself is just a `task`, meaning it's naturally suspendable. The `wait` call seamlessly pauses execution without polluting the whole `main` function with `async` keywords.
3. **Structured Intent:** `out.debug`, `out.error`, and `out.write` give semantic meaning to what the terminal is doing, rather than just dumping everything into a global `print()`.
4. **Clean Error Control:** The `check` block elegantly intercepts the Type Union `[WeatherData, Error]`, forcing the developer to acknowledge that a network call could fail, without relying on a clunky `try/catch` block.