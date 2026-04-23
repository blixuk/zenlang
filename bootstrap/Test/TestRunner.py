import os
import re
from typing import List, Dict, Any
from Parser.AST import FunctionStatement, BlockStatement, CallExpression, Identifier
from Interpreter.Interpreter import Interpreter, ReturnException
from Lexer.Lexer import Lexer
from Parser.Parser import Parser

class TestRunner:
    def __init__(self, compiler):
        self.compiler = compiler
        ast = compiler.ast_typed or compiler.ast
        self.interpreter = Interpreter(ast, compiler.source_path, debug=compiler.debug, resolver=compiler.resolver)
        self.results = []

    def run_file(self, path: str):
        print(f"--- Running tests in {path} ---")
        # The compiler should have already parsed and validated the whole program (merged AST)
        ast = self.compiler.ast_typed or self.compiler.ast
        if not ast:
            print(f"No AST available in compiler for {path}")
            return

        # Setup interpreter with the global environment from the compiler
        self.interpreter.global_environment = self.compiler.get_global_environment()
        self.interpreter.source_path = path
        
        found_tests = 0
        passed = 0
        
        # Only run tests belonging to the file we are currently interested in
        # (Since ast.statements contains all merged statements)
        abs_target_path = os.path.abspath(path)
        
        for stmt in ast.statements:
            # We check filename attribute if it exists
            stmt_filename = getattr(stmt, "filename", None)
            if stmt_filename and os.path.abspath(stmt_filename) != abs_target_path:
                continue
                
            if isinstance(stmt, FunctionStatement):
                # 1. Traditional test_ functions
                if stmt.name.startswith("test_"):
                    found_tests += 1
                    if self._run_test_function(stmt):
                        passed += 1
                
                # 2. Doctests from documentation
                if stmt.documentation:
                    doctests = self._extract_doctests(stmt.documentation)
                    for doctest in doctests:
                        found_tests += 1
                        if self._run_doctest(doctest, stmt.name):
                            passed += 1

        print(f"--- {path}: {passed}/{found_tests} tests passed ---")
        return passed == found_tests if found_tests > 0 else True

    def _run_test_function(self, func: FunctionStatement) -> bool:
        print(f"  [TEST] {func.name}...", end=" ", flush=True)
        try:
            # Call the function: func()
            ident = Identifier(func.line, func.column, func.scope_level, func.name, "Identifier")
            call = CallExpression(func.line, func.column, func.scope_level, ident, [])
            result = self.interpreter.evaluate(call, self.interpreter.global_environment)
            if result is False:
                print("FAIL: Returned false")
                return False
            print("PASS")
            return True
        except Exception as e:
            msg = str(e)
            if hasattr(e, "value"): msg = str(e.value)
            print(f"FAIL: {msg}")
            return False

    def _extract_doctests(self, doc: str) -> List[str]:
        # Simple extraction of @example blocks
        doctests = []
        lines = doc.split("\n")
        in_example = False
        current_example = []
        
        for line in lines:
            trimmed = line.strip()
            # Remove /! and !/ if present in the raw comment
            if trimmed.startswith("/!"): trimmed = trimmed[2:].strip()
            if trimmed.endswith("!/"): trimmed = trimmed[:-2].strip()
            
            if trimmed.startswith("@example"):
                in_example = True
                continue
            if in_example:
                if trimmed.startswith("@") or "!/" in line:
                    if current_example:
                        doctests.append(self._dedent("\n".join(current_example)))
                        current_example = []
                    in_example = False
                else:
                    current_example.append(line)
        
        if current_example:
            doctests.append(self._dedent("\n".join(current_example)))
            
        return doctests

    def _dedent(self, code: str) -> str:
        lines = code.split("\n")
        if not lines: return ""
        
        # Find minimum indentation of non-empty lines
        min_indent = None
        for line in lines:
            if not line.strip(): continue
            indent = len(line) - len(line.lstrip())
            if min_indent is None or indent < min_indent:
                min_indent = indent
        
        if min_indent is None: return code
        
        return "\n".join(line[min_indent:] if len(line) >= min_indent else line.lstrip() for line in lines)

    def _run_doctest(self, code: str, func_name: str) -> bool:
        print(f"  [DOC ] {func_name} example...", end=" ", flush=True)
        try:
            # Parse the doctest code snippet
            lexer = Lexer(code, f"doctest_{func_name}")
            tokens = lexer.tokenize()
            parser = Parser(tokens, f"doctest_{func_name}")
            ast = parser.parse()
            
            # Execute each statement in the doctest
            result = None
            for stmt in ast.statements:
                result = self.interpreter.evaluate(stmt, self.interpreter.global_environment)
                
            if result is False:
                print("FAIL: Returned false")
                return False
            print("PASS")
            return True
        except Exception as e:
            msg = str(e)
            if hasattr(e, "value"): msg = str(e.value)
            print(f"FAIL: {msg}")
            return False
