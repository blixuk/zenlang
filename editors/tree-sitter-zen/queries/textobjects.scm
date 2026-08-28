(function_declaration
  body: (block) @function.inside) @function.around

(class_declaration
  body: (block) @class.inside) @class.around

(structure_declaration) @class.around

(doc_comment) @comment.around
(line_comment) @comment.around
(block_comment) @comment.around
