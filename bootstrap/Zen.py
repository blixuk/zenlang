import argparse
import json
import os
import sys

sys.setrecursionlimit(1000000)
from typing import List, Optional

from Checker.SemanticChecker import SemanticChecker
from Checker.TypeChecker import TypeChecker
from Interpreter.Interpreter import Interpreter, ReturnException
from Lexer.Lexer import Lexer
from Logging.Dumper import ast_to_json
from Module.DependencyGraph import DependencyGraph
from Module.Resolver import Resolver
from Parser.AST import ASTNode, ImportStatement, FromImportStatement
from Parser.Parser import Parser
from REPL.REPL import REPL

class ZenCompiler:
    
    def __init__(self, debug: bool = False):
        self.debug: bool = debug
        self.source_path: Optional[str] = None
        self.output_path: Optional[str] = None
        self.source: Optional[str] = None
        self.tokens: Optional[list] = None
        self.ast: Optional[ASTNode] = None
        self.ast_typed: Optional[ASTNode] = None
        
        self.resolver = Resolver()
        self.resolver.search_paths.append("src")
        self.resolver.search_paths.append("lib")
        self.graph = DependencyGraph()
        self.modules: dict[str, ASTNode] = {} # path -> AST

    def load_source(self, path: str) -> None:
        self.source_path = path
        if self.debug:
            print(f"-- LOADING SOURCE: {path} --")
        try:
            with open(path, "r") as file:
                self.source = file.read()
        except FileNotFoundError:
            print(f"Error: File '{path}' not found.")
            sys.exit(1)

    def tokenize(self) -> None:
        if not self.source:
            return
            
        if self.debug:
            print("-- LEXING TOKENS -- ")
            
        lexer: Lexer = Lexer(self.source, self.source_path, strict=True, debug=self.debug)
        self.tokens = lexer.tokenize()
        
        if self.debug:
            lexer.logger.print_debugs()
        lexer.logger.print_errors()

    def parse_file(self, path: str) -> Optional[ASTNode]:
        if path in self.modules:
            return self.modules[path]

            
        if self.debug:
            print(f"-- PARSING MODULE: {path} --")
            
        try:
            with open(path, "r") as file:
                source = file.read()
        except FileNotFoundError:
            print(f"Error: File '{path}' not found.")
            sys.exit(1)
            
        lexer = Lexer(source, path, strict=True, debug=self.debug)
        tokens = lexer.tokenize()
        if lexer.logger.has_errors:
            lexer.logger.print_errors()
            sys.exit(1)
            
        print(f"DEBUG: Parsing {path} (bootstrap)...", flush=True)
        parser = Parser(tokens, path, strict=True, debug=self.debug)
        ast = parser.parse()
        print(f"DEBUG: Parsed {path}. Statements: {len(ast.statements)}", flush=True)
        if parser.logger.has_errors:
            parser.logger.print_errors()
            sys.exit(1)
            
        self.modules[path] = ast
        self.graph.add_node(path)
        
        # Scan for imports
        for statement in ast.statements:
            if isinstance(statement, (ImportStatement, FromImportStatement)):
                import_path = getattr(statement, "path")
                
                try:
                    resolved_path = self.resolver.resolve(import_path, os.path.dirname(path))
                    if resolved_path not in self.modules:
                         self.graph.add_edge(path, resolved_path)
                         self.parse_file(resolved_path) # Recurse
                    else:
                         self.graph.add_edge(path, resolved_path)
                except FileNotFoundError as e:
                    print(f"Import Error in {path}: {e}")
                    sys.exit(1)
                    
        return ast

    def parse(self) -> None:
        if not self.source_path:
            return

        # Start recursive parsing from main source
        # We need absolute path for graph
        abs_path = os.path.abspath(self.source_path)
        
        main_ast = self.parse_file(abs_path)
        self.ast = main_ast
        
        # Merge ASTs?
        # For monolithic build, we want to prepend all module ASTs to the main AST.
        # But topological order is crucial.
        
        compilation_order = self.graph.get_compilation_order()
        if self.debug:
            print(f"DEBUG: Compilation Order: {compilation_order}")
            print(f"-- COMPILATION ORDER: {compilation_order} --")
            
        # Collect all statements
        merged_statements = []
        for path in compilation_order:
            if self.debug: print(f"DEBUG: Checking path: {path} vs abs_path: {abs_path}")
            if path == abs_path: continue # Add main last or handle separately
            module_ast = self.modules[path]
            merged_statements.extend(module_ast.statements)
            
        # Add main statements last
        merged_statements.extend(main_ast.statements)
        
        # Update main AST
        self.ast.statements = merged_statements
        
        if self.debug:
            token_type_count = 0
            for s in merged_statements:
                if hasattr(s, "name") and hasattr(s.name, "value") and s.name.value == "TokenType":
                    token_type_count += 1
            print(f"DEBUG: Found {token_type_count} declarations of TokenType in merged AST")

    def validate(self) -> None:
        if not self.ast:
            return

        if self.debug:
            print("-- CHECKING TYPES -- ")
            
        sys.setrecursionlimit(1000000)
        typechecker = TypeChecker(self.ast, self.source_path, debug=self.debug)
        self.ast_typed = typechecker.check_program()
        
        if self.debug:
            # typechecker.logger.print_debugs()
            pass
        # typechecker.logger.print_errors()

        if self.ast_typed:
            if self.debug:
                print("-- CHECKING SEMANTICS -- ")
            semanticchecker: SemanticChecker = SemanticChecker(
                self.ast_typed, self.source_path, debug=self.debug
            )
            self.ast_typed = semanticchecker.check_program()
            
            if self.debug:
                 # semanticchecker.logger.print_debugs()
                 pass
            # semanticchecker.logger.print_errors()

    def interpret(self, arguments: List[str]) -> None:
        if not self.ast_typed:
            if self.debug:
                print("Skipping interpretation (Analysis failed or skipped)")
            return

        if self.debug:
            print("-- RUNNING INTERPRETER -- ")
            
        interpreter: Interpreter = Interpreter(self.ast_typed, self.source_path, debug=self.debug, resolver=self.resolver)
        try:
            result: any = interpreter.interpret(arguments=arguments)
            # Auto-call zen_entry if it exists in the global environment
            if "zen_entry" in interpreter.global_environment.values:
                func = interpreter.global_environment.get("zen_entry")
                interpreter._call_function(func, [])
            
            if self.debug:
                print()
                print("RESULT: ", result)
            return result
        except ReturnException as return_exception:
            return f"Return value: '{return_exception.value}'"

    def generate(self) -> None:
        if not self.ast_typed:
            return
            
        from Transpiler.CodeGenerator import Generator
        from Transpiler.CCompile import CCompiler

        if self.debug:
            print("-- RUNNING CODE GENERATOR -- ")
        generator = Generator()
        result: str = generator.generate(self.ast_typed)
        
        if self.debug:
            print()
            print("RESULT: ")
            print(result)
            print("-- RUNNING C COMPILER -- ")
            
        ccompiler = CCompiler()
        ccompiler.compile(result)

        if self.debug:
            print("-- RUNNING PROGRAM -- ")
        # ccompiler.run() happens inside compile currently

    def write_output(self) -> None:
        if self.debug:
            print("-- WRITING OUTPUT -- ")

        if not os.path.exists("output"):
            os.makedirs("output")

        if self.tokens:
            with open("output/tokens.ztok", "w") as f:
                f.write(str(self.tokens))

        if self.ast:
            with open("output/AST.zast", "w") as f:
                f.write(str(self.ast))
            with open("output/AST.json", "w") as f:
                f.write(json.dumps(ast_to_json(self.ast), indent=2))

        if self.ast_typed:
            with open("output/AST_TYPED.zast", "w") as f:
                f.write(str(self.ast_typed))
            with open("output/AST_TYPED.json", "w") as f:
                f.write(json.dumps(ast_to_json(self.ast_typed), indent=2))

def main():
    sys.setrecursionlimit(50000)

    parser = argparse.ArgumentParser(description="ZenLang Compiler/Interpreter")
    parser.add_argument("source", nargs="?", help="Source file path")
    parser.add_argument("args", nargs="*", help="Arguments passed to the script")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--repl", action="store_true", help="Start REPL")
    parser.add_argument("--interpret", action="store_true", help="Interpret the source code (default)")
    parser.add_argument("--generate", action="store_true", help="Generate and compile C code")
    
    # We use parse_known_args because 'args' might capture flags meant for the script?
    # Actually, argparse handles remaining args well if configured.
    # Zen.py [options] source [script_args]
    
    args, script_args = parser.parse_known_args()

    # Prioritize REPL
    if args.repl:
        repl = REPL()
        repl.run()
        return

    # Check for Source
    if not args.source:
        # If no source and no REPL, show help
        parser.print_help()
        return

    debug = args.debug or args.verbose
    compiler = ZenCompiler(debug=debug)
    compiler.output_path = args.output
    compiler.load_source(args.source)
    
    # Pipeline
    compiler.tokenize()
    compiler.parse()
    compiler.validate()
    
    # Execution Mode
    if args.generate:
        compiler.generate()
    else:
        # Default to interpret
        # Pass remaining arguments to interpreter
        # We need to construct argv: [script_path, source_to_compile, result_path]
        # args.source is the script path (../src/zen.zl)
        # args.args is [output_path] (../build/zen.c)
        # We need to pass [args.source] + args.args? 
        # But zen_entry expects args[1] to be source.
        # So we need [args.source, args.source] + args.args
        
        interpreter_args = [args.source] + args.args
        compiler.interpret(interpreter_args)
        
    # Optional: Write debug output
    if debug:
        compiler.write_output()

if __name__ == "__main__":
    main()
