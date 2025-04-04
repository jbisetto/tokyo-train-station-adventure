# Project Reorganization Checklist

## Step 1: Create Backup
- [ ] Create a git branch for the reorganization (`git checkout -b reorganize-project-structure`)
- [ ] Commit current state before making any changes (`git add . && git commit -m "Save state before reorganization"`)

## Step 2: Consolidate Data Directories
- [ ] Create necessary subdirectories in backend/data if they don't exist
  - [ ] `mkdir -p backend/data/profiles`
  - [ ] `mkdir -p backend/data/prompt_templates`
  - [ ] `mkdir -p backend/data/schemas`
  - [ ] `mkdir -p backend/data/player_history`
  - [ ] `mkdir -p backend/data/usage`
- [ ] Move profile data to backend
  - [ ] `mv profiles/* backend/data/profiles/`
  - [ ] Remove empty profiles directory: `rmdir profiles`
- [ ] Move prompt templates to backend
  - [ ] `mv prompt_templates/* backend/data/prompt_templates/`
  - [ ] Remove empty prompt_templates directory: `rmdir prompt_templates`
- [ ] Move schemas to backend
  - [ ] `mv schemas/* backend/data/schemas/`
  - [ ] Remove empty schemas directory: `rmdir schemas`
- [ ] Move data directory contents to backend
  - [ ] `mv data/player_history/* backend/data/player_history/`
  - [ ] `mv data/usage/* backend/data/usage/`
  - [ ] Remove empty data directory: `rmdir data/player_history data/usage data`

## Step 3: Consolidate Tests
- [ ] Create necessary subdirectories in backend/tests if they don't exist
  - [ ] `mkdir -p backend/tests/fixtures`
  - [ ] `mkdir -p backend/tests/unit`
  - [ ] `mkdir -p backend/tests/integration`
- [ ] Move test files from root to appropriate backend locations
  - [ ] `mv test_bedrock.py backend/tests/integration/`
  - [ ] `mv test_ollama_integration.py backend/tests/integration/`
  - [ ] `mv test_ollama_simple.py backend/tests/integration/`
- [ ] Move test_cache_dir to backend if needed
  - [ ] `mv test_cache_dir backend/tests/`
- [ ] Consolidate test fixtures and configuration
  - [ ] Compare and merge `tests/fixtures` with `backend/tests/fixtures` if needed
  - [ ] Compare and merge `tests/conftest.py` with `backend/tests/conftest.py` if needed
  - [ ] Move unique test scripts: `mv tests/*.py backend/tests/` (excluding duplicates)
- [ ] Move testing utilities
  - [ ] `mv run_tests.sh backend/`
  - [ ] `mv pytest.ini backend/`
  - [ ] `mv tests/run_all_tests.sh backend/tests/`
- [ ] Remove redundant root tests directory: `rm -rf tests` (after ensuring all content is safely moved)

## Step 4: Consolidate Configuration
- [ ] Move configuration directory
  - [ ] `mkdir -p backend/config` (if it doesn't exist)
  - [ ] `mv config/* backend/config/`
  - [ ] Remove empty config directory: `rmdir config`
- [ ] Copy environment variables to backend
  - [ ] `cp .env backend/` (keeping the root copy if needed for top-level scripts)
- [ ] Consolidate requirements
  - [ ] Compare and merge root `requirements.txt` with `backend/requirements.txt`
  - [ ] Update `backend/requirements.txt` with any missing dependencies

## Step 5: Handle Python Files
- [ ] Compare root `main.py` with `backend/main.py`
  - [ ] Merge functionality if needed
  - [ ] Remove duplicate at root: `rm main.py`
- [ ] Move any other Python modules at root level to appropriate backend locations
  - [ ] Review each `.py` file and determine proper location
  - [ ] Move to appropriate subdirectory in backend

## Step 6: Handle Additional Directories
- [ ] Move simulator directory to backend
  - [ ] `mkdir -p backend/simulator`
  - [ ] `mv simulator/* backend/simulator/`
  - [ ] Remove empty simulator directory: `rmdir simulator`
- [ ] Move examples directory to backend
  - [ ] `mkdir -p backend/examples`
  - [ ] `mv examples/* backend/examples/`
  - [ ] Remove empty examples directory: `rmdir examples`
- [ ] Handle tokyo-py virtual environment
  - [ ] Determine if tokyo-py is a virtual environment or actual code
  - [ ] If it's a virtual environment, add to .gitignore and exclude from reorganization
  - [ ] If it contains project code, move to appropriate location: `mv tokyo-py backend/tokyo-py`
- [ ] Check for any other directories at root level that should be moved to backend

## Step 7: Update Documentation
- [ ] Update README.md to reflect new project structure
- [ ] Document any changed import paths or file locations
- [ ] Create a migration guide if the reorganization affects other developers
- [ ] Move project-specific documentation to `backend/docs/` if not already there
  - [ ] Move markdown files like `TEST_REORGANIZATION.md`, `test_reorganization_plan.md`, `README-DEEPSEEK-OLLAMA.md` to `backend/docs/`

## Step 8: Update Import Statements
- [ ] Scan all Python files for imports that need updating due to moved files
  - [ ] Use a tool like `grep -r "from " --include="*.py" backend/` to find all import statements
  - [ ] Use `grep -r "import " --include="*.py" backend/` to find additional imports
  - [ ] Update import paths in affected files
- [ ] Pay special attention to cross-directory imports that may break

## Step 9: Update File References
- [ ] Check for hardcoded file paths that may need updating
  - [ ] Look for `open()` calls, `os.path` usages, etc.
  - [ ] Update any absolute or relative paths that refer to moved files

## Step 10: Test the Reorganized Structure
- [ ] Run all tests to ensure they pass: `cd backend && ./run_tests.sh`
- [ ] Verify the application starts correctly: `cd backend && python main.py`
- [ ] Check for any runtime errors related to missing files or incorrect paths
- [ ] Test simulator functionality: `cd backend && python -m simulator.app`
- [ ] Test any examples to ensure they still work

## Step 11: Update .gitignore
- [ ] Update `.gitignore` to reflect the new directory structure
  - [ ] Remove entries for directories that no longer exist at root
  - [ ] Add entries for new directory structure
  - [ ] Ensure virtual environments are properly ignored

## Step 12: Create Script for Running from Root (Optional)
- [ ] Create a simple shell script in the root to run the backend application
  - [ ] `echo '#!/bin/bash\ncd backend && python main.py' > run.sh && chmod +x run.sh`
- [ ] Consider creating other convenience scripts for common operations

## Step 13: Commit and Review
- [ ] Commit changes: `git add . && git commit -m "Reorganize project structure"`
- [ ] Push changes to remote: `git push origin reorganize-project-structure`
- [ ] Create a pull request for review
- [ ] Address any feedback from review

## Step 14: Documentation Updates
- [ ] Update any external documentation that refers to the old structure
- [ ] Update CI/CD pipeline configurations if needed
- [ ] Update deployment scripts if they reference specific file paths

## Step 15: Final Cleanup
- [ ] Remove any temporary files created during the reorganization
- [ ] Remove any now-empty directories
- [ ] Final check for any overlooked files that should be moved

## Step 16: Release and Communication
- [ ] Tag a new release after the reorganization is complete
- [ ] Communicate changes to all team members
- [ ] Provide guidance on how to adapt to the new structure 