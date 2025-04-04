# Project Reorganization Checklist

## Step 1: Create Backup
- [x] Create a git branch for the reorganization (`git checkout -b reorganize-project-structure`)
- [x] Commit current state before making any changes (`git add . && git commit -m "Save state before reorganization"`)

## Step 2: Rename Backend to Src
- [x] First run tests to verify current state: `./run_tests.sh`
- [x] Rename the backend directory to src: `mv backend src`
- [x] Update main imports in root-level files that might reference backend
  - [x] `grep -r "from backend" --include="*.py" .` to find references
  - [x] `grep -r "import backend" --include="*.py" .` to find additional references
  - [x] Update these critical imports to use 'src' instead
- [x] Run tests after renaming to ensure basic functionality still works: `./run_tests.sh`
- [x] Commit this initial change: `git add . && git commit -m "Rename backend directory to src"`

## Step 3: Consolidate Data Directories
- [x] Create necessary subdirectories in src/data if they don't exist
  - [x] `mkdir -p src/data/profiles`
  - [x] `mkdir -p src/data/prompt_templates`
  - [x] `mkdir -p src/data/schemas`
  - [x] `mkdir -p src/data/player_history`
  - [x] `mkdir -p src/data/usage`
- [x] Move profile data to src
  - [x] `mv profiles/* src/data/profiles/`
  - [x] Remove empty profiles directory: `rmdir profiles`
- [x] Move prompt templates to src
  - [x] `mv prompt_templates/* src/data/prompt_templates/`
  - [x] Remove empty prompt_templates directory: `rmdir prompt_templates`
- [x] Move schemas to src
  - [x] `mv schemas/* src/data/schemas/`
  - [x] Remove empty schemas directory: `rmdir schemas`
- [x] Move data directory contents to src
  - [x] `mv data/player_history/* src/data/player_history/`
  - [x] `mv data/usage/* src/data/usage/`
  - [x] Remove empty data directory: `rmdir data/player_history && rmdir data/usage && rmdir data`

## Step 4: Consolidate Tests
- [x] Create necessary subdirectories in src/tests if they don't exist
  - [x] `mkdir -p src/tests/fixtures`
  - [x] `mkdir -p src/tests/unit`
  - [x] `mkdir -p src/tests/integration`
- [x] Move test files from root to appropriate src locations
  - [x] `mv test_bedrock.py src/tests/integration/`
  - [x] `mv test_ollama_integration.py src/tests/integration/`
  - [x] `mv test_ollama_simple.py src/tests/integration/`
  - [x] `mv test_reorganization_plan.md src/docs/`
- [x] Move test_cache_dir to src if needed
  - [x] `mv test_cache_dir src/tests/`
- [x] Consolidate test fixtures and configuration
  - [x] Compare and merge `tests/fixtures` with `src/tests/fixtures` if needed
  - [x] Compare and merge `tests/conftest.py` with `src/tests/conftest.py` if needed
  - [x] Move unique test scripts: `mv tests/example_prompt.py src/tests/` and others as needed
- [x] Move testing utilities
  - [x] `mv run_tests.sh src/`
  - [x] `mv pytest.ini src/`
  - [x] `mv tests/run_all_tests.sh src/tests/`
- [x] Migrate all test files from tests/ to src/tests/
  - [x] Create all necessary subdirectories in src/tests/ to match appropriate source code structure:
    - [x] `mkdir -p src/tests/backend/ai/companion/{core,tier1,tier2,tier3,integration,learning,personality,utils,vector}`
    - [x] `mkdir -p src/tests/backend/api`
    - [x] `mkdir -p src/tests/integration/{tier2,tier3}`
    - [x] `mkdir -p src/tests/data/player_history`
  - [x] Copy all test files, transforming "backend" to "src" in the directory structure:
    - [x] `rsync -av --include="*/" --include="*.py" --exclude="*" tests/backend/ src/tests/backend/`
    - [x] `rsync -av --include="*/" --include="*.py" --exclude="*" tests/data/ src/tests/data/`
  - [x] Update src/run_tests.sh to point to src/tests/:
    - [x] Change `python3 -m pytest tests/ -v` to `python3 -m pytest src/tests/ -v`
  - [x] Update src/pytest.ini to use the new tests location:
    - [x] Change `testpaths = ../tests` to `testpaths = tests`
  - [x] Update src/tests/run_all_tests.sh to use the new path structure (change backend/ references to src/)
  - [x] Run tests from new location to verify everything works:
    - [x] `cd src && ./run_tests.sh`
    - [x] Fix any path-related issues that arise
  - [x] Update imports in test files: 
    - [x] Find all imports referencing 'backend': `grep -r "from backend" --include="*.py" src/tests/`
    - [x] Update these imports to reference 'src' instead
- [x] Remove redundant root tests directory: `rm -rf tests` (after ensuring all content is safely moved)

## Step 5: Consolidate Configuration
- [x] Move configuration directory
  - [x] `mkdir -p src/config` (if it doesn't exist)
  - [x] `mv config/* src/config/`
  - [x] Remove empty config directory: `rmdir config`
- [x] Copy environment variables to src
  - [x] `cp .env src/` (keeping the root copy if needed for top-level scripts)
- [x] Consolidate requirements
  - [x] Compare and merge root `requirements.txt` with `src/requirements.txt`
  - [x] Update `src/requirements.txt` with any missing dependencies

## Step 6: Handle Python Files
- [x] Compare root `main.py` with `src/main.py`
  - [x] Merge functionality if needed
  - [x] Remove duplicate at root: `rm main.py`
- [x] Move any other Python modules at root level to appropriate src locations
  - [x] Move `__pycache__` directory: `mv __pycache__ src/` (if needed)
  - [x] Move any other `.py` files to appropriate subdirectories

## Step 7: Handle Additional Directories
- [x] Handle simulator directory
  - [x] Simulator directory removed (to be recreated later)
- [x] Handle examples directory
  - [x] Examples directory removed
- [x] Move docs directory to src (if not already there)
  - [x] `mkdir -p src/docs` (if it doesn't exist)
  - [x] `mv docs/* src/docs/`
  - [x] Remove empty docs directory: `rmdir docs`
- [x] Handle tokyo-py virtual environment
  - [x] Confirm it's a virtual environment: `cat tokyo-py/pyvenv.cfg`
  - [x] Add to .gitignore (already seems to be ignored) and exclude from reorganization
- [x] Fix paths in configuration files
  - [x] Update log file path in src/main.py to use an absolute path in the src directory
  - [x] Remove any existing backend.log files from root directory

## Step 8: Update Documentation
- [x] Update README.md to reflect new project structure
- [x] Document any changed import paths or file locations
- [x] Move project-specific documentation to `src/docs/` if not already done
  - [x] Move markdown files like `TEST_REORGANIZATION.md` to `src/docs/`
  - [x] Move `README-DEEPSEEK-OLLAMA.md` to `src/docs/`

## Step 9: Update Import Statements
- [ ] Scan all Python files for imports that need updating due to moved files
  - [ ] Use `grep -r "from " --include="*.py" src/` to find all import statements
  - [ ] Use `grep -r "import " --include="*.py" src/` to find additional imports
  - [ ] Update import paths in affected files
- [ ] Pay special attention to cross-directory imports that may break
- [ ] Update any imports that reference `backend` to use `src` instead

## Step 10: Update File References
- [ ] Check for hardcoded file paths that may need updating
  - [ ] Look for file operations: `grep -r "open(" --include="*.py" src/`
  - [ ] Look for path operations: `grep -r "os.path" --include="*.py" src/`
  - [ ] Update any absolute or relative paths that refer to moved files
  - [ ] Replace any 'backend/' path references with 'src/'

## Step 11: Test the Reorganized Structure
- [ ] Run tests to ensure they pass: `cd src && python -m pytest`
- [ ] Verify the application starts correctly: `cd src && python main.py`
- [ ] Check for any runtime errors related to missing files or incorrect paths
- [ ] Test simulator functionality: `cd src && python -m simulator.app`
- [ ] Test any examples to ensure they still work

## Step 12: Update .gitignore
- [ ] Update `.gitignore` to reflect the new directory structure
  - [ ] Remove entries for directories that no longer exist at root
  - [ ] Add entries for new directory structure
  - [ ] Ensure virtual environments are properly ignored
  - [ ] Replace any 'backend/' references with 'src/'

## Step 13: Create Script for Running from Root (Optional)
- [ ] Create a simple shell script in the root to run the src application
  - [ ] `echo '#!/bin/bash\ncd src && python main.py' > run.sh && chmod +x run.sh`
- [ ] Consider creating other convenience scripts for common operations

## Step 14: Commit and Review
- [ ] Commit changes: `git add . && git commit -m "Reorganize project structure"`
- [ ] Push changes to remote: `git push origin reorganize-project-structure`
- [ ] Create a pull request for review
- [ ] Address any feedback from review

## Step 15: Documentation Updates
- [ ] Update any external documentation that refers to the old structure
- [ ] Update CI/CD pipeline configurations if needed
- [ ] Update deployment scripts if they reference specific file paths

## Step 16: Final Cleanup
- [ ] Remove any temporary files created during the reorganization
- [ ] Remove any now-empty directories
- [ ] Final check for any overlooked files that should be moved

## Step 17: Release and Communication
- [ ] Tag a new release after the reorganization is complete
- [ ] Communicate changes to all team members
- [ ] Provide guidance on how to adapt to the new structure