import sys
import os

# Add bootstrap to path
sys.path.append(os.path.join(os.getcwd(), "bootstrap"))

from Zen import ZenCompiler
from Transpiler.SMIRGenerator import SMIRGenerator

def test_smir(source_code: str):
    compiler = ZenCompiler(debug=False)
    # We can use a temporary file or mock the loader
    with open("temp_smir.zl", "w") as f:
        f.write(source_code)
    
    compiler.load_source("temp_smir.zl")
    compiler.tokenize()
    compiler.parse()
    compiler.validate() # This runs TypeChecker and SemanticChecker
    
    generator = SMIRGenerator()
    instructions = generator.generate(compiler.ast_typed)
    
    print("=== S-MIR OUTPUT ===")
    for inst in instructions:
        print(inst)
    print("====================")
    
    os.remove("temp_smir.zl")

if __name__ == "__main__":
    code = """
    function main() {
        let x -> 10
        do while x > 0 {
            x -> x - 1
            when x < 5 {
                print(`small`)
            } or when x == 7 {
                print(`seven`)
            } or {
                print(`large`)
            }
        }
        return x
    }
    """
    test_smir(code)
