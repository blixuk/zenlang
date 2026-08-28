/**
 * Tree-sitter grammar for Zenlang (MVP — highlighting / outline oriented).
 * Not a full formal language parser; prioritizes robust tokenization of real code.
 */
module.exports = grammar({
  name: 'zen',

  extras: $ => [
    /\s/,
    $.line_comment,
    $.block_comment,
  ],

  conflicts: $ => [],

  word: $ => $.identifier,

  rules: {
    source_file: $ => repeat($._statement),

    _statement: $ => choice(
      $.doc_comment,
      $.import_statement,
      $.export_statement,
      $.function_declaration,
      $.structure_declaration,
      $.class_declaration,
      $.enumerator_declaration,
      $.task_declaration,
      $.let_statement,
      $.set_statement,
      $.when_statement,
      $.do_statement,
      $.return_statement,
      $.break_statement,
      $.continue_statement,
      $.assert_statement,
      $.expression_statement,
      $.block,
    ),

    // Doc: /! ... !/
    doc_comment: $ => token(seq('/!', /([^!]|![^/])*/, '!/')),

    // Line comment: // ...
    line_comment: _ => token(/\/\/[^\n]*/),

    // Block comment: /* ... */
    block_comment: _ => token(/\/\*[\s\S]*?\*\//),

    import_statement: $ => seq(
      optional('from'),
      'import',
      choice($.module_path, $.string),
      optional(seq('as', $.identifier)),
      optional(';'),
    ),

    export_statement: $ => seq(
      'export',
      choice(
        $.function_declaration,
        $.let_statement,
        $.set_statement,
        $.structure_declaration,
        $.class_declaration,
        $.identifier,
      ),
    ),

    module_path: $ => prec.right(seq(
      $.identifier,
      repeat(seq('.', $.identifier)),
    )),

    function_declaration: $ => prec(2, seq(
      'function',
      field('name', $.identifier),
      field('parameters', $.parameter_list),
      optional(seq(':', field('return_type', $._type))),
      field('body', $.block),
    )),

    parameter_list: $ => seq(
      '(',
      optional(seq(
        $.parameter,
        repeat(seq(',', $.parameter)),
        optional(','),
      )),
      ')',
    ),

    parameter: $ => seq(
      field('name', $.identifier),
      optional(seq(':', field('type', $._type))),
    ),

    structure_declaration: $ => seq(
      'structure',
      field('name', $.identifier),
      '{',
      repeat($.field_declaration),
      '}',
    ),

    class_declaration: $ => seq(
      'class',
      field('name', $.identifier),
      optional(seq('extends', $.identifier)),
      field('body', $.block),
    ),

    enumerator_declaration: $ => seq(
      'enumerator',
      field('name', $.identifier),
      '{',
      optional(seq(
        $.identifier,
        repeat(seq(',', $.identifier)),
        optional(','),
      )),
      '}',
    ),

    task_declaration: $ => seq(
      'task',
      field('name', $.identifier),
      field('body', $.block),
    ),

    field_declaration: $ => seq(
      field('name', $.identifier),
      ':',
      field('type', $._type),
      optional(','),
    ),

    let_statement: $ => seq(
      'let',
      field('name', $.identifier),
      optional(seq(choice(':', ':>'), field('type', $._type))),
      optional(seq('->', field('value', $._expression))),
      optional(';'),
    ),

    set_statement: $ => seq(
      'set',
      field('name', $.identifier),
      optional(seq(choice(':', ':>'), field('type', $._type))),
      optional(seq('->', field('value', $._expression))),
      optional(';'),
    ),

    when_statement: $ => prec.right(seq(
      'when',
      field('condition', $._expression),
      field('consequence', $.block),
      repeat(seq('or', 'when', $._expression, $.block)),
      optional(seq('or', $.block)),
    )),

    do_statement: $ => choice(
      seq('do', 'while', field('condition', $._expression), field('body', $.block)),
      seq('do', 'until', field('condition', $._expression), field('body', $.block)),
      seq('do', 'for', field('name', $.identifier), 'in', field('iterable', $._expression), field('body', $.block)),
      seq('do', field('body', $.block), 'while', field('condition', $._expression)),
    ),

    return_statement: $ => prec.right(seq(
      choice('<-', 'return'),
      optional(field('value', $._expression)),
    )),

    break_statement: $ => seq('break', optional(';')),
    continue_statement: $ => seq('continue', optional(';')),
    assert_statement: $ => seq(choice('!', 'assert'), field('condition', $._expression), optional(';')),

    expression_statement: $ => seq($._expression, optional(';')),

    // Prefer block in statement position; map_literal wins in expression via prec
    block: $ => prec.right(1, seq('{', repeat($._statement), '}')),

    _type: $ => choice(
      $.generic_type,
      $.type_name,
    ),

    type_name: $ => $.identifier,

    generic_type: $ => prec(2, seq(
      $.identifier,
      '[',
      $._type,
      repeat(seq(',', $._type)),
      ']',
    )),

    _expression: $ => choice(
      $.assignment_expression,
      $.binary_expression,
      $.unary_expression,
      $.call_expression,
      $.index_expression,
      $.member_expression,
      $.primary,
    ),

    assignment_expression: $ => prec.right(1, seq(
      field('left', choice($.identifier, $.member_expression, $.index_expression)),
      field('operator', choice('->', ':>')),
      field('right', $._expression),
    )),

    binary_expression: $ => {
      const table = [
        ['or', 2],
        ['and', 3],
        ['==', 4], ['!=', 4], ['<', 4], ['<=', 4], ['>', 4], ['>=', 4], ['is', 4],
        ['..', 5], ['..=', 5],
        ['+', 6], ['-', 6],
        ['*', 7], ['/', 7], ['%', 7],
      ];
      return choice(...table.map(([op, precedence]) =>
        prec.left(precedence, seq(
          field('left', $._expression),
          field('operator', op),
          field('right', $._expression),
        ))
      ));
    },

    unary_expression: $ => prec(8, seq(
      field('operator', choice('not', '-', '!')),
      field('argument', $._expression),
    )),

    call_expression: $ => prec(9, seq(
      field('function', $._expression),
      field('arguments', $.argument_list),
    )),

    argument_list: $ => seq(
      '(',
      optional(seq(
        $._expression,
        repeat(seq(',', $._expression)),
        optional(','),
      )),
      ')',
    ),

    index_expression: $ => prec(10, seq(
      field('object', $._expression),
      '[',
      field('index', $._expression),
      ']',
    )),

    member_expression: $ => prec(10, seq(
      field('object', $._expression),
      '.',
      field('property', $.identifier),
    )),

    primary: $ => choice(
      $.identifier,
      $.number,
      $.string,
      $.boolean,
      $.nothing,
      $.list_literal,
      $.map_literal,
      $.lambda,
      $.structure_literal,
      seq('(', $._expression, ')'),
    ),

    lambda: $ => prec(1, seq(
      'function',
      $.parameter_list,
      $.block,
    )),

    structure_literal: $ => prec(2, seq(
      field('name', $.identifier),
      '{',
      optional(seq(
        $.field_initializer,
        repeat(seq(',', $.field_initializer)),
        optional(','),
      )),
      '}',
    )),

    field_initializer: $ => seq(
      field('name', $.identifier),
      '->',
      field('value', $._expression),
    ),

    list_literal: $ => seq(
      '[',
      optional(seq(
        $._expression,
        repeat(seq(',', $._expression)),
        optional(','),
      )),
      ']',
    ),

    map_literal: $ => prec(2, seq(
      '{',
      optional(seq(
        $.map_entry,
        repeat(seq(',', $.map_entry)),
        optional(','),
      )),
      '}',
    )),

    map_entry: $ => seq(
      field('key', choice($.string, $.identifier)),
      '->',
      field('value', $._expression),
    ),

    boolean: $ => choice('True', 'False'),
    nothing: $ => choice('nothing', 'Nothing', 'Void'),

    number: $ => token(choice(
      /0[xX][0-9a-fA-F_]+/,
      /0[bB][01_]+/,
      /\d[\d_]*\.\d[\d_]*([eE][+-]?\d+)?/,
      /\d[\d_]*([eE][+-]?\d+)?/,
    )),

    string: $ => token(seq(
      optional(/[a-zA-Z_][a-zA-Z0-9_]*/),
      '`',
      repeat(choice(/[^`\\]/, /\\./)),
      '`',
    )),

    identifier: $ => /[a-zA-Z_][a-zA-Z0-9_]*/,
  },
});
