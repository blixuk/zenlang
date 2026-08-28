; Zenlang Tree-sitter highlights (also used by Zed)

(doc_comment) @comment.doc
(line_comment) @comment
(block_comment) @comment

(string) @string
(number) @number
(boolean) @boolean
(nothing) @constant.builtin

[
  "let"
  "set"
  "function"
  "class"
  "structure"
  "enumerator"
  "import"
  "use"
  "from"
  "as"
  "export"
  "when"
  "or"
  "and"
  "not"
  "do"
  "while"
  "until"
  "for"
  "in"
  "return"
  "break"
  "continue"
  "task"
  "extends"
  "is"
  "assert"
] @keyword

[
  "->"
  "<-"
  ":>"
  ".."
  "..="
  "=="
  "!="
  "<"
  "<="
  ">"
  ">="
  "+"
  "-"
  "*"
  "/"
  "%"
  "!"
] @operator

(function_declaration
  name: (identifier) @function)

(parameter
  name: (identifier) @variable.parameter)

(structure_declaration
  name: (identifier) @type)

(class_declaration
  name: (identifier) @type)

(enumerator_declaration
  name: (identifier) @type)

(call_expression
  function: (identifier) @function)

(member_expression
  property: (identifier) @property)

(type_name
  (identifier) @type)

(generic_type
  (identifier) @type)

(structure_literal
  name: (identifier) @type)

(field_declaration
  name: (identifier) @property)

(field_initializer
  name: (identifier) @property)

(map_entry
  key: (string) @property)

[
  "("
  ")"
  "["
  "]"
  "{"
  "}"
] @punctuation.bracket

[
  ","
  ";"
  "."
  ":"
] @punctuation.delimiter

(identifier) @variable
