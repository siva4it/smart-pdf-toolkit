#!/usr/bin/env python3
"""
Script to fix syntax errors in security test files.
"""

import os
import re
from pathlib import Path

def fix_syntax_errors():
    """Fix common syntax errors in security test files."""
    security_dir = Path("tests/security")
    
    for py_file in security_dir.glob("*.py"):
        if py_file.name.startswith("test_"):
            print(f"Fixing {py_file}")
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Fix escaped quotes in f-strings
                content = re.sub(r'f\\"([^"]*)\\"', r'f"\1"', content)
                
                # Fix escaped quotes in regular strings
                content = re.sub(r'\\"([^"]*)\\"', r'"\1"', content)
                
                # Fix unterminated strings by ensuring proper quote matching
                lines = content.split('\n')
                fixed_lines = []
                
                for line in lines:
                    # Skip empty lines
                    if not line.strip():
                        fixed_lines.append(line)
                        continue
                        
                    # Fix common patterns
                    if 'f"' in line and line.count('"') % 2 != 0:
                        # Try to fix unterminated f-strings
                        if line.rstrip().endswith('\\'):
                            line = line.rstrip()[:-1] + '"'
                    
                    # Fix docstrings with incorrect escaping
                    if '"""' in line and '\\"' in line:
                        line = line.replace('\\"', '"')
                    
                    fixed_lines.append(line)
                
                fixed_content = '\n'.join(fixed_lines)
                
                # Write back the fixed content
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                    
                print(f"Fixed {py_file}")
                
            except Exception as e:
                print(f"Error fixing {py_file}: {e}")

if __name__ == "__main__":
    fix_syntax_errors()