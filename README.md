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
    - Configurable parameters via API for temperature, top_p, etc.
    - Japanese language correction features
  - Amazon Bedrock APIs for complex scenarios (10% of interactions)
  - Scenario detection system for specialized handling of common player requests
- **Data Storage**: SQLite with Google/Facebook OAuth integration
- **Communication**: Event-based architecture with domain events
- **API**: RESTful API with comprehensive endpoints for game functionality

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

## API Documentation

The backend provides a comprehensive REST API for game functionality:

### Core Endpoints

- **Companion Assist**: `POST /api/companion/assist` - Get assistance from the companion dog
- **Dialogue Processing**: `POST /api/dialogue/process` - Process dialogue exchanges
- **Game State**: `POST /api/game/state`, `GET /api/game/state/{player_id}` - Save/load game progress
- **NPC Interaction**: Various endpoints for NPC information and dialogue
- **DeepSeek Engine**: `POST /api/npc/engine/parameters` - Configure the AI language model

Full API documentation is available at `/api/docs` when running the server.

## Development Plan

1. **Phase 1**: Japanese language processing prototype with DeepSeek 7B
2. **Phase 2**: Core game mechanics and station environment
3. **Phase 3**: Companion assistance features
4. **Phase 4**: Learning progress analytics and achievements

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 16+
- SQLite

### Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/tokyo-train-station-adventure.git
   cd tokyo-train-station-adventure
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv tokyo-py
   source tokyo-py/bin/activate  # On Windows: tokyo-py\Scripts\activate
   pip install -r requirements.txt
   ```

3. Start the backend server:
   ```bash
   python -m backend.main
   ```

4. Access the API documentation at http://localhost:8000/api/docs

## Testing

The project includes comprehensive tests for all components:

### Running Backend Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/backend/api/test_deepseek_parameters.py

# Run with verbose output
python -m pytest -v
```

For more detailed testing information, see the [Testing README](tests/README.md).

## License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

