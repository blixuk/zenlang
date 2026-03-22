```c

let item : Tuple<String, Integer> -> ( key : String, value : Integer )
let item : Tuple -> ( key : String, value : Integer )

// if using a name, you must supply a type or a value
let item : Tuple -> ( key : Nothing, value : Nothing )
let item -> ( key : Nothing, value : Nothing )

let weapon -> item( `sword`, 100 )
let weapon : Tuple -> item( key -> `sword`, value -> 100 )

print(weapon[0])
print(weapon[1])
print(weapon.key)
print(weapon.value)

let shape : Tuple<Integer, Integer, Integer> -> (x: 0, y: 0, z: 0)
let shape -> (x: 0, y: 0, z: 0)

print(shape.x, shape.y)

let thing -> (1, 2, 3)

```
