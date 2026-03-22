import os
import re

ROOT_DIR = '/mnt/personal/programming/Python/2025/zen'

# Regex patterns
# Pattern 1: `from `path` import`
# Capture group 1 is the path inside backticks
FROM_PATTERN = re.compile(r'from `([^`]+)` import')

# Pattern 2: `import `path``
# Capture group 1 is the path inside backticks
# Note: we need to be careful not to match other things, but `import ` usually signifies this.
IMPORT_PATTERN = re.compile(r'import `([^`]+)`')

def refactor_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Replace `from `path` import` -> `from path import`
    content = FROM_PATTERN.sub(r'from \1 import', content)
    
    # Replace `import `path`` -> `import path`
    content = IMPORT_PATTERN.sub(r'import \1', content)
    
    if content != original_content:
        print(f"Refactoring {filepath}...")
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    count = 0
    for root, dirs, files in os.walk(ROOT_DIR):
        if 'venv' in dirs:
            dirs.remove('venv') # Skip venv
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
            
        for file in files:
            if file.endswith('.zl') or file.endswith('.zen'):
                filepath = os.path.join(root, file)
                if refactor_file(filepath):
                    count += 1
    
    print(f"Refactored {count} files.")

if __name__ == '__main__':
    main()
