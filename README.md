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
- **Context-Aware AI Responses**: Vector database for relevant game world knowledge

## Technical Architecture

- **Frontend**: Phaser.js running on HTML5 Canvas for pixel art rendering
- **Backend**: Python with FastAPI for game logic and AI integration
- **AI Processing**: 
  - Three-tier processing system with full configurability:
    - **Tier 1**: Rule-based systems (Default: handles 70% of interactions)
    - **Tier 2**: Local Ollama with DeepSeek 7B model (Default: handles 20% of interactions)
      - Configurable parameters via API for temperature, top_p, etc.
      - Japanese language correction features
    - **Tier 3**: Amazon Bedrock APIs (Default: handles 10% of complex scenarios)
  - Individual tiers can be enabled/disabled via configuration
  - System can be set to exclusively use a single tier
  - Default behavior uses automatic routing based on request complexity
  - Runtime tier selection API for development and testing purposes
  - Strict topic guardrails to ensure responses stay on-topic:
    - Limited to Japanese language (JLPT N5), station navigation, and game mechanics
    - Automatic redirection of off-topic questions back to game-relevant topics
    - Character-appropriate boundary enforcement that maintains immersion
  - Scenario detection system for specialized handling of common player requests
- **Knowledge Management**:
  - ChromaDB vector database for semantic search of game world knowledge
  - Conversation history tracking for contextual responses
  - Integration of conversation context and world knowledge in AI prompts
- **Data Storage**: SQLite with Google/Facebook OAuth integration
- **Communication**: Event-based architecture with domain events
- **API**: RESTful API with comprehensive endpoints for game functionality

## Repository Structure

```
tokyo-train-station-adventure/
├── frontend/                         # Phaser.js frontend
├── backend/                          # Python backend
│   ├── ai/                           # AI components
│   │   ├── companion/                # Companion dog AI
│   │   │   ├── core/                 # Core AI components
│   │   │   │   ├── vector/           # Vector database integration
│   │   │   │   ├── storage/          # Conversation storage
│   │   │   │   └── models/           # Data models
├── shared/                           # Shared code/types
├── assets/                           # Raw game assets
├── tools/                            # Development and build tools
├── infrastructure/                   # Deployment configurations
└── docs/                             # Project documentation
```

## AI Companion System

The game's companion dog uses a sophisticated AI system to provide context-aware assistance:

1. **Tiered Processing**: Requests are classified by complexity and routed to appropriate AI tiers
2. **Conversation Management**: Tracks conversation history to provide coherent multi-turn responses
3. **Vector Knowledge Store**: Uses ChromaDB to retrieve relevant game world information
4. **Contextual Prompting**: Combines conversation context and knowledge base data for accurate responses, with strict topic guardrails that keep interactions focused on game-relevant topics

The system is designed to be efficient, using local models where possible and only calling cloud APIs for complex interactions. Content guardrails ensure all interactions remain focused on language learning, station navigation, and game mechanics, redirecting off-topic questions in a character-appropriate way that enhances rather than breaks immersion.

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
5. **Phase 5**: Vector database integration for context-aware responses

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 16+
- SQLite
- Sentence Transformers (for vector embeddings)
- ChromaDB

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

# Run vector database tests
python -m pytest tests/backend/ai/companion/core/vector/

# Run with verbose output
python -m pytest -v
```

For more detailed testing information, see the [Testing README](tests/README.md).

## License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

