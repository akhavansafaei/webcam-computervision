#!/usr/bin/env python3
"""
Script to add file path as a comment to the first line of each Python file
in the project directory and all subdirectories.
"""

import os
import sys
from pathlib import Path

def add_path_to_python_file(file_path):
    """
    Add the file path as a comment to the first line of a Python file.
    
    Args:
        file_path (Path): Path to the Python file
    """
    try:
        # Read the existing content
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Get relative path from project root
        relative_path = file_path.relative_to(Path.cwd())
        path_comment = f"# File: {relative_path}\n"
        
        # Check if the first line already contains a path comment
        if lines and lines[0].startswith("# File: "):
            # Replace the existing path comment
            lines[0] = path_comment
        else:
            # Add the path comment as the first line
            lines.insert(0, path_comment)
        
        # Write the modified content back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"✅ Updated: {relative_path}")
        
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")

def find_and_process_python_files(root_dir=None):
    """
    Find all Python files in the project and add path comments.
    
    Args:
        root_dir (str, optional): Root directory to search. Defaults to current directory.
    """
    if root_dir is None:
        root_dir = Path.cwd()
    else:
        root_dir = Path(root_dir)
    
    if not root_dir.exists():
        print(f"❌ Directory {root_dir} does not exist!")
        return
    
    print(f"🔍 Searching for Python files in: {root_dir}")
    print("-" * 50)
    
    # Find all Python files recursively
    python_files = list(root_dir.rglob("*.py"))
    
    if not python_files:
        print("No Python files found in the directory.")
        return
    
    print(f"Found {len(python_files)} Python file(s)")
    print("-" * 50)
    
    # Process each Python file
    for py_file in python_files:
        # Skip this script itself to avoid modifying it while running
        if py_file.name == Path(__file__).name:
            print(f"⏭️  Skipped: {py_file.relative_to(root_dir)} (current script)")
            continue
            
        add_path_to_python_file(py_file)
    
    print("-" * 50)
    print(f"✨ Finished processing {len(python_files)} files!")

def main():
    """Main function to run the script."""
    print("Python File Path Adder")
    print("=" * 50)
    
    # Get the directory to process (default to current directory)
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = None
    
    try:
        find_and_process_python_files(target_dir)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()