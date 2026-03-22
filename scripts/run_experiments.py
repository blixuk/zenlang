import os
import subprocess
import sys

# Define the root directory for tests
TESTS_DIR = os.path.abspath("tests")
INTERPRETER = "Zen.py"

def run_test(file_path):
    """
    Runs a single ZenLang test file.
    Returns (success, output) tuple.
    """
    try:
        # Run the test file using the ZenLang interpreter
        result = subprocess.run(
            [sys.executable, INTERPRETER, file_path],
            capture_output=True,
            text=True,
            timeout=10 # 10 seconds timeout per test
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr + "\n" + result.stdout
            
    except subprocess.TimeoutExpired:
        return False, "Timeout expired"
    except Exception as e:
        return False, str(e)

def main():
    print(f"Running tests in {TESTS_DIR}...")
    
    passed = 0
    failed = 0
    test_files = []

    # Find all .zl files in tests directory
    for root, dirnames, filenames in os.walk(TESTS_DIR):
        for filename in filenames:
            if filename.endswith(".zl") or filename.endswith(".zen"): # Support both extensions
                # Skip known failing tests or tests that require input
                if filename in ["test.zen", "io_input_output.zl"]:
                    continue
                test_files.append(os.path.join(root, filename))

    test_files.sort()
    
    failed_files = []
    
    # Run each test
    for test_file in test_files:
        relative_path = os.path.relpath(test_file, os.getcwd())
        print(f"Running {relative_path}...", end=" ", flush=True)
        
        success, output = run_test(test_file)
        
        if success:
            print("PASS")
            passed += 1
        else:
            print("FAIL")
            print("-" * 40)
            print(f"Error output for {relative_path}:")
            print(output.strip())
            print("-" * 40)
            failed += 1
            failed_files.append(relative_path)

    print("\n" + "=" * 40)
    print(f"Test Summary: {passed} Passed, {failed} Failed, {len(test_files)} Total")
    
    if failed_files:
        print("\nFailed Files:")
        for f in failed_files:
            print(f"- {f}")
            
    print("=" * 40)

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
