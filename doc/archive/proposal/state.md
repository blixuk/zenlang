```c
// State Machine
// sets the state when a condition is met
// defualt sate is always Nothing unless set
state identifer {
    identifer -> when <condition> { .... },
    identifer -> when <condition>
} defualt { .... }

state player {
    walking -> when <condition> { .... },
    idle -> when <condition>,
}

player.state()
```
