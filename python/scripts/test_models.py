#!/usr/bin/env python3
"""
Test script to validate generated models
"""
import ast
import sys
from pathlib import Path


def check_syntax(file_path: Path) -> bool:
    """Check if a Python file has valid syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source, filename=str(file_path))
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return False


def main():
    """Main function"""
    project_root = Path(__file__).parent.parent
    models_dir = project_root / 'app' / 'models'
    
    print("Checking model files syntax...")
    print(f"Models directory: {models_dir}\n")
    
    model_files = list(models_dir.rglob('*.py'))
    model_files = [f for f in model_files if f.name != '__init__.py']
    
    total = len(model_files)
    passed = 0
    failed = 0
    
    for model_file in sorted(model_files):
        if check_syntax(model_file):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Total model files: {total}")
    print(f"✓ Passed: {passed}")
    if failed > 0:
        print(f"✗ Failed: {failed}")
    print(f"{'='*50}")
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n✓ All model files have valid syntax!")


if __name__ == '__main__':
    main()

