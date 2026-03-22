import os
import re

ROOT_DIR = '/mnt/personal/programming/Python/2025/zen/tests'

# 1. Replace `print(...)` with `write(...)`
#    And ensure `from zen.io import write` is present if `write` is used.
PRINT_PATTERN = re.compile(r'\bprint\(')

# 2. Replace `if ... {` with `when ... {`
#    Note: `if` might be used in comments or strings, so simple replace is risky but likely okay for tests.
#    Strictly: `if` followed by space/condition.
IF_PATTERN = re.compile(r'\bif\b')

# 3. Replace `} else {` with `} or {`
ELIF_PATTERN = re.compile(r'\}\s*else\s*\{')

def needs_io_import(content):
    if "write(" in content or "read(" in content:
        if "zen.io" not in content:
            return True
    return False

def refactor_file(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Skipping binary file: {filepath}")
        return False
    
    original_content = content
    
    # Replace print -> write
    if "print(" in content:
        content = PRINT_PATTERN.sub('write(', content)
    
    # Replace if -> when
    # Be careful not to replace inside strings.
    # For now, regex replacement for `if ` -> `when ` might be safer.
    # Actually, `if` is keyword.
    # Let's simple replace ` if ` with ` when ` and `if (` with `when (`
    # But `do if` exists in loops.zl, which I changed manually.
    # Let's use a systematic approach.
    
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        # Very naive checking to avoid strings (not perfect)
        # Assuming tests are simple enough.
        
        # Replace `print` -> `write`
        if "print(" in line and "`" not in line.split("print(")[0]: # Avoid print inside string
             line = line.replace("print(", "write(")

        # Replace `if` -> `when`
        # Check if it's not inside a string
        # Match standalone word `if`
        # Using regex substitution on line
        if not line.strip().startswith("//"):
             line = re.sub(r'\bif\b', 'when', line)
             line = re.sub(r'\belse\b', 'or', line)
        
        new_lines.append(line)
        
    content = '\n'.join(new_lines)
    
    # Add import if needed
    if "write(" in content and "from zen.io import write" not in content and "import zen.io" not in content:
        # Add to top
        content = "from zen.io import write\n" + content
        
    if content != original_content:
        print(f"Refactoring {filepath}...")
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    count = 0
    for root, dirs, files in os.walk(ROOT_DIR):
        for file in files:
            if file.endswith('.zl') or file.endswith('.zen'):
                filepath = os.path.join(root, file)
                if refactor_file(filepath):
                    count += 1
    
    print(f"Refactored {count} files.")

if __name__ == '__main__':
    main()
