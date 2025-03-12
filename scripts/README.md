# Development Scripts

This directory contains scripts to help with development tasks for the Tokyo Train Station Adventure project.

## Test Organization Scripts

### `move_tests_to_root.py`

This script helps maintain the project's test organization by moving tests from module-specific test directories (e.g., `backend/tests/`) to the root `tests/` directory while preserving the module structure.

Usage:
```bash
python scripts/move_tests_to_root.py [--dry-run]
```

Options:
- `--dry-run`: Show what would be done without actually moving files

Example:
```bash
# Show what would be done without moving files
python scripts/move_tests_to_root.py --dry-run

# Actually move the files
python scripts/move_tests_to_root.py
```

## Git Hooks

### `git-hooks/pre-commit`

This pre-commit hook checks for tests in module-specific test directories and reminds developers to place tests in the root `tests/` directory.

To install:
```bash
cp scripts/git-hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

This hook will prevent commits that add tests to module-specific test directories. To bypass this check (not recommended), use git commit with `--no-verify`.

## Why Use the Root `tests/` Directory?

Using a root `tests/` directory with a structure that mirrors the project structure has several benefits:

1. **Consistency**: All tests are in one place, making it easier to find and run them.
2. **Separation of Concerns**: Tests are separate from the code they test, reducing the risk of test code being imported in production.
3. **Easier Test Discovery**: Test runners can easily find all tests in one directory.
4. **Cleaner Project Structure**: The main code directories are not cluttered with test files.
5. **Simplified Imports**: Tests can import the code they test using the same import paths as the rest of the project.

For more details, see the [Test Organization](../docs/design/development-workflow.md#test-organization) section in the development workflow documentation. 