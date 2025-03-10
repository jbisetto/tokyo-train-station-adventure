![Tokyo Train Station Adventure Banner](assets/images/banner.jpeg)

# Tokyo Train Station Adventure

A language learning game that helps players learn Japanese through an immersive pixel art adventure. The player, an English speaker with JLPT N5 level Japanese knowledge, navigates a Tokyo train station with a bilingual companion dog to purchase a ticket to Odawara.

## Project Overview

The Tokyo Train Station Adventure is designed to make Japanese language learning fun and practical through an immersive gaming experience. Players navigate a realistic Tokyo train station environment, interacting with station staff, ticket machines, and other travelers while being assisted by a helpful bilingual dog companion.

### Key Features

- **Immersive Pixel Art Environment**: Navigate through a detailed Tokyo train station
- **Practical Language Learning**: Focus on real-world Japanese usage in train stations
- **Bilingual Dog Companion**: Get assistance and translations from your companion
- **Tiered AI Approach**: Optimized for performance and cost with local-first processing
- **Progress Tracking**: Monitor your Japanese language acquisition

## Technical Architecture

- **Frontend**: Phaser.js running on HTML5 Canvas for pixel art rendering
- **Backend**: Python with FastAPI for game logic and AI integration
- **AI Processing**: 
  - Rule-based systems (70% of interactions)
  - Local Ollama with DeepSeek 7B model (20% of interactions)
  - Amazon Bedrock APIs for complex scenarios (10% of interactions)
- **Data Storage**: SQLite with Google/Facebook OAuth integration
- **Communication**: Event-based architecture with domain events

## Repository Structure

```
tokyo-train-station-adventure/
├── frontend/                         # Phaser.js frontend
├── backend/                          # Python backend
├── shared/                           # Shared code/types
├── assets/                           # Raw game assets
├── tools/                            # Development and build tools
├── infrastructure/                   # Deployment configurations
└── docs/                             # Project documentation
```

## Development Plan

1. **Phase 1**: Japanese language processing prototype with DeepSeek 7B
2. **Phase 2**: Core game mechanics and station environment
3. **Phase 3**: Companion assistance features
4. **Phase 4**: Learning progress analytics and achievements

## Getting Started

*Development setup instructions will be added as the project progresses.*

## Testing

The project follows a Test-Driven Development (TDD) approach, with comprehensive test coverage for all components. The tests are organized to match the module structure of the codebase.

### Setting Up the Test Environment

1. Create and activate a virtual environment:
   ```bash
   python -m venv tokyo-py
   source tokyo-py/bin/activate  # On Windows: tokyo-py\Scripts\activate
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   Alternatively, you can install the testing dependencies directly:
   ```bash
   pip install pytest pytest-asyncio pytest-cov pytest-mock pyyaml aiohttp boto3
   ```

### Running Tests

- Run all tests:
  ```bash
  python -m pytest
  ```

- Run tests for a specific module:
  ```bash
  python -m pytest tests/backend/ai/companion/tier3/
  ```

- Run a specific test file:
  ```bash
  python -m pytest tests/backend/ai/companion/tier3/test_tier3_processor.py
  ```

- Run a specific test:
  ```bash
  python -m pytest tests/backend/ai/companion/tier3/test_tier3_processor.py::TestTier3Processor::test_process
  ```

- Run tests with verbose output:
  ```bash
  python -m pytest -v
  ```

- Run tests with coverage report:
  ```bash
  python -m pytest --cov=backend
  ```

### Test Structure

The test suite is organized to mirror the structure of the codebase:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test interactions between components
- **Functional Tests**: Test complete workflows

Each module in the companion AI system has corresponding test files that verify its functionality:

```
tests/
└── backend/
    └── ai/
        └── companion/
            ├── core/              # Tests for core components
            ├── tier1/             # Tests for rule-based processing
            ├── tier2/             # Tests for local LLM integration
            ├── tier3/             # Tests for cloud API integration
            └── utils/             # Tests for utility functions
```

### Continuous Integration

The project uses a shell script to run all tests as part of the development workflow:

```bash
./run_tests.sh
```

This script runs the full test suite and generates a coverage report.
