# Zenlang C Runtime Naming Conventions

All C functions in the Zenlang bootstrap runtime should follow a consistent naming convention:
`Zen<Subject>_<Verb>[_<Object>]`

## Examples

| Zenlang | C Runtime |
|---------|-----------|
| `Map.has(k)` | `ZenMap_has_key(map, key)` |
| `Set.add(v)` | `ZenSet_add_value(set, value)` |
| `List.at(i)` | `ZenList_get_at_index(list, index)` |
| `String.at(i)` | `ZenString_get_character_at_index(str, index)` |
| `IO.write(v)` | `ZenIO_write_value(v)` |

## Rules

1. **Full Names**: Use `integer` instead of `int`, `string` instead of `str`, `value` instead of `val`.
2. **Subject First**: The first part of the name must be the type it operates on (e.g., `ZenMap`, `ZenList`).
3. **Verb Second**: The action being performed (e.g., `has`, `add`, `get`).
4. **Object Third (Optional)**: What the action is performed on (e.g., `key`, `value`, `index`).
5. **CamelCase Type, snake_case Action**: `ZenMap_has_key`.
