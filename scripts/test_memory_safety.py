import sys
import os

# Add bootstrap to path
sys.path.append(os.path.join(os.getcwd(), 'bootstrap'))

from Zen import ZenCompiler
from Transpiler.SMIRGenerator import SMIRGenerator
from Transpiler.SMIRAnalyzer import SMIRAnalyzer

def test_memory_safety(code):
    print(f"Testing code:\n{code}")
    compiler = ZenCompiler(debug=False)
    with open("temp_memory.zl", "w") as f:
        f.write(code)
    
    compiler.load_source("temp_memory.zl")
    compiler.tokenize()
    compiler.parse()
    from Checker.TypeChecker import TypeChecker
    checker = TypeChecker(compiler.ast, compiler.source_path, debug=False)
    compiler.ast_typed = checker.check_program()
    
    generator = SMIRGenerator()
    instructions = generator.generate(compiler.ast_typed)
    
    analyzer = SMIRAnalyzer(instructions, checker.scope.global_region)
    
    print("--- BEFORE ANALYSIS ---")
    for instr in instructions:
        print(instr)
        
    print("--- REGION TREE ---")
    checker.scope.global_region.print_tree()
    
    try:
        analyzer.analyze()
        print("--- AFTER ANALYSIS ---")
        for instr in instructions:
            print(instr)
        print("Analysis successful (no errors).")
    except Exception as e:
        print(f"Analysis Failed: {e}")

if __name__ == "__main__":
    print("=== TEST 1: Use After Move ===")
    test_memory_safety("""
    function main() {
        let x -> 10
        let y -> x
        print(x)
    }
    """)
    
    print("\n=== TEST 2: Promotion on Return ===")
    test_memory_safety("""
    function get_val() {
        let x -> 42
        return x
    }
    """)

    print("\n=== TEST 3: CFG Branch Safety ===")
    test_memory_safety("""
    function main() {
        let x -> 10
        when x > 5 {
            let y -> x
        }
        print(x) // This SHOULD be an error if we follow all paths?
                 // Actually, if x is only moved in one branch, it's moved in the merge point.
    }
    """)
