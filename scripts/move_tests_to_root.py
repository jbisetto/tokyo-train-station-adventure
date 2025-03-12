#!/usr/bin/env python3
"""
Script to move tests from module-specific test directories to the root tests directory.

This script helps maintain the project's test organization by moving tests from
module-specific test directories (e.g., backend/tests/) to the root tests directory
while preserving the module structure.

Usage:
    python scripts/move_tests_to_root.py [--dry-run]

Options:
    --dry-run    Show what would be done without actually moving files
"""

import os
import shutil
import argparse
from pathlib import Path


def find_test_files(base_dir):
    """Find all test files in module-specific test directories."""
    test_files = []
    
    # Walk through the directory structure
    for root, dirs, files in os.walk(base_dir):
        # Skip the root tests directory
        if root.startswith(os.path.join(base_dir, 'tests')):
            continue
            
        # Check if this is a module-specific tests directory
        if os.path.basename(root) == 'tests':
            module_path = os.path.relpath(os.path.dirname(root), base_dir)
            
            # Find all Python files in this directory
            for file in files:
                if file.endswith('.py'):
                    source_path = os.path.join(root, file)
                    # Determine the target path in the root tests directory
                    target_dir = os.path.join(base_dir, 'tests', module_path)
                    target_path = os.path.join(target_dir, file)
                    
                    test_files.append((source_path, target_path))
                    
            # Recursively search subdirectories
            for dir_name in dirs:
                subdir = os.path.join(root, dir_name)
                submodule_path = os.path.join(module_path, dir_name)
                
                for subroot, subdirs, subfiles in os.walk(subdir):
                    rel_path = os.path.relpath(subroot, os.path.join(root, dir_name))
                    for file in subfiles:
                        if file.endswith('.py'):
                            source_path = os.path.join(subroot, file)
                            target_dir = os.path.join(base_dir, 'tests', module_path, dir_name, rel_path)
                            target_path = os.path.join(target_dir, file)
                            
                            test_files.append((source_path, target_path))
    
    return test_files


def move_test_files(test_files, dry_run=False):
    """Move test files from source to target paths."""
    for source_path, target_path in test_files:
        # Create the target directory if it doesn't exist
        target_dir = os.path.dirname(target_path)
        
        if dry_run:
            print(f"Would move {source_path} to {target_path}")
            print(f"Would create directory {target_dir} if it doesn't exist")
        else:
            print(f"Moving {source_path} to {target_path}")
            
            # Create the target directory if it doesn't exist
            os.makedirs(target_dir, exist_ok=True)
            
            # Copy the file to the target path
            shutil.copy2(source_path, target_path)
            
            # Check if the file was copied successfully
            if os.path.exists(target_path):
                # Remove the source file
                os.remove(source_path)
                print(f"Successfully moved {source_path} to {target_path}")
            else:
                print(f"Failed to move {source_path} to {target_path}")


def main():
    """Main function to move tests to the root tests directory."""
    parser = argparse.ArgumentParser(description='Move tests to the root tests directory')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without actually moving files')
    args = parser.parse_args()
    
    # Get the project root directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Find all test files in module-specific test directories
    test_files = find_test_files(base_dir)
    
    if not test_files:
        print("No test files found in module-specific test directories.")
        return
    
    print(f"Found {len(test_files)} test files to move.")
    
    # Move the test files
    move_test_files(test_files, dry_run=args.dry_run)
    
    if args.dry_run:
        print("\nThis was a dry run. No files were actually moved.")
    else:
        print("\nAll test files have been moved to the root tests directory.")
        print("Remember to update any imports in the moved files to reflect their new location.")


if __name__ == '__main__':
    main() 