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

  conflicts: $ => [
    [$.assignment_statement, $.map_entry],
  ],

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
      $.assignment_statement,
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

    import_statement: $ => choice(
      seq(
        optional('extern'),
        'from',
        choice($.module_path, $.string),
        choice('import', 'use'),
        seq($.identifier, repeat(seq(',', $.identifier))),
        optional(';'),
      ),
      seq(
        optional('extern'),
        choice('import', 'use'),
        choice($.module_path, $.string),
        optional(seq('as', $.identifier)),
        optional(';'),
      ),
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
      choice(
        seq(
          optional(seq(':', field('return_type', $._type))),
          optional(field('parameters', $.parameter_list)),
        ),
        seq(
          optional(field('parameters', $.parameter_list)),
          optional(seq(':', field('return_type', $._type))),
        ),
      ),
      field('body', choice(
        $.block,
        seq('->', field('expression', $._expression)),
        seq('<-', field('expression', $._expression)),
      )),
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

    assignment_statement: $ => seq(
      field('left', choice($.identifier, $.member_expression, $.index_expression)),
      field('operator', choice('->', ':>', '<~')),
      field('right', $._expression),
      optional(';'),
    ),

    _expression: $ => choice(
      $.binary_expression,
      $.unary_expression,
      $.call_expression,
      $.index_expression,
      $.member_expression,
      $.primary,
    ),

    binary_expression: $ => {
      const table = [
        ['|>', 2],
        ['??', 2],
        ['or', 2],
        ['and', 3],
        ['==', 4], ['!=', 4], ['<', 4], ['<=', 4], ['>', 4], ['>=', 4], ['is', 4], ['<:', 4], ['in', 4],
        ['..', 5], ['..=', 5], ['...', 5], ['..+', 5], ['..-', 5],
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
      $.list_comprehension,
      $.list_literal,
      $.map_comprehension,
      $.map_literal,
      $.lambda,
      $.structure_literal,
      seq('(', $._expression, ')'),
    ),

    lambda: $ => prec(1, seq(
      'function',
      optional($.parameter_list),
      optional(seq(':', field('return_type', $._type))),
      field('body', choice(
        $.block,
        seq('->', field('expression', $._expression)),
        seq('<-', field('expression', $._expression)),
      )),
    )),

    structure_literal: $ => prec(2, seq(
      field('name', $.type_identifier),
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

    spread_element: $ => seq(
      '...',
      field('value', $._expression),
    ),

    list_comprehension: $ => prec(3, seq(
      '[',
      'for',
      field('variable', choice(
        $.identifier,
        seq($.identifier, ',', $.identifier),
      )),
      'in',
      field('iterable', $._expression),
      optional(seq('when', field('condition', $._expression))),
      '->',
      field('body', $._expression),
      ']',
    )),

    list_literal: $ => seq(
      '[',
      optional(seq(
        choice($._expression, $.spread_element),
        repeat(seq(',', choice($._expression, $.spread_element))),
        optional(','),
      )),
      ']',
    ),

    map_comprehension: $ => prec(3, seq(
      '{',
      'for',
      field('variable', choice(
        $.identifier,
        seq($.identifier, ',', $.identifier),
      )),
      'in',
      field('iterable', $._expression),
      optional(seq('when', field('condition', $._expression))),
      '->',
      field('key', $._expression),
      choice(':', '->'),
      field('value', $._expression),
      '}',
    )),

    map_literal: $ => prec(2, seq(
      '{',
      optional(seq(
        choice($.map_entry, $.spread_element),
        repeat(seq(',', choice($.map_entry, $.spread_element))),
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
    nothing: $ => choice('nothing', 'Nothing', 'Void', 'Default', 'default'),

    number: $ => token(choice(
      /0[xX][0-9a-fA-F_]+/,
      /0[bB][01_]+/,
      /0[oO][0-7_]+/,
      /\d[\d_]*\.\d[\d_]*([eE][+-]?\d+)?/,
      /\d[\d_]*([eE][+-]?\d+)?/,
    )),

    string: $ => token(choice(
      seq(
        optional(/[a-zA-Z_][a-zA-Z0-9_]*/),
        '`',
        repeat(choice(/[^`\\]/, /\\./)),
        '`',
      ),
      seq(
        '```',
        repeat(choice(/[^`\\]/, /\\./, /`[^`]/, /``[^`]/)),
        '```',
      ),
      seq(
        '"',
        repeat(choice(/[^"\\]/, /\\./)),
        '"',
      ),
    )),

    type_identifier: $ => token(/[A-Z][a-zA-Z0-9_]*/),
    identifier: $ => /[a-zA-Z_][a-zA-Z0-9_]*/,
  },
});
