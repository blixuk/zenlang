```c

enumerator name { .... }

enumerator Direction { North, South, East, West }

print(Direction)
// ( (`North`, 0), (`South`, 1), (`East`, 2), (`West`, 3) )

enumerator Direction { 
    North -> 1, 
    South -> 2, 
    East -> 3, 
    West -> 4 
}

print(Direction)
// ( (`North`, 1), (`South`, 2), (`East`, 3), (`West`, 4) )
print(Direction.names)
// ( `North`, `South`, `East`, `West` )
print(Direction.values)
// ( 1, 2, 3, 4 )
print(Direction.South)
// (`South`, 2)
print(Direction.South.name)
// `South`
print(Direction.South.value)
// 2

enumerator Week { 
    SUNDAY -> -1, 
    MONDAY -> 1, 
    TUESDAY -> 10, 
    WEDNESDAY -> 100 
}
print(Direction)
// ( (`SUNDAY`, -1), (`MONDAY`, 1), (`TUESDAY`, 10), (`WEDNESDAY`, 100) )

enumerator Week { 
    SUNDAY -> 10, 
    MONDAY -> auto, 
    TUESDAY -> auto, 
    WEDNESDAY -> auto 
}
// ( (`SUNDAY`, 10), (`MONDAY`, 11), (`TUESDAY`, 12), (`WEDNESDAY`, 13) )

```
