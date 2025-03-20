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
- **Data Storage**: 
  - Current: In-memory dictionaries for development and testing
  - Planned: SQLite with Google/Facebook OAuth integration
- **Communication**: 
  - Planned: Event-based architecture with domain events
  - Current: Direct function calls between components
- **API**: RESTful API with comprehensive endpoints (mock implementations)

## Repository Structure

Current project structure:

```
tokyo-train-station-adventure/
├── frontend/                         # Phaser.js frontend (in development)
├── backend/                          # Python backend 
│   ├── ai/                           # AI components (fully implemented)
│   │   └── companion/                # Companion dog AI
│   │       └── core/                 # Core AI components
│   │           ├── vector/           # Vector database integration
│   │           ├── storage/          # Conversation storage
│   │           └── models/           # Data models
│   ├── api/                          # API endpoints (mock implementations)
│   │   └── routers/                  # API routes for game functionality
│   ├── data/                         # Data access layer (in-memory implementations)
│   ├── game_core/                    # Game mechanics (planned implementation)
│   └── domain/                       # Domain models and business logic (planned)
└── docs/                             # Project documentation
    ├── design/                       # Design documents
    ├── pm/                           # Project management docs
    └── ui/                           # UI documentation
```

**Implementation Notes:**
- AI components are fully implemented with functioning vector database integration
- API endpoints are defined but currently use mock implementations
- Game logic is currently placeholder with planned future implementation
- Data is stored in-memory with database integration planned for later phases

**Planned Future Components:**
```
tokyo-train-station-adventure/
├── shared/                           # Shared code/types
├── assets/                           # Raw game assets
├── tools/                            # Development and build tools
└── infrastructure/                   # Deployment configurations
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

1. **Phase 1**: Japanese language processing prototype with vector database integration
2. **Phase 2**: Core game mechanics and station environment
3. **Phase 3**: Companion assistance features
4. **Phase 4**: Learning progress analytics and achievements
5. **Phase 5**: Vector database integration for context-aware responses

## Current Development Status

- ✅ **Phase 1**: Japanese language processing prototype with vector database integration
- ✅ **Phase 5**: Vector database integration for context-aware responses is complete
- 🔄 **Phase 3**: Companion assistance features are under active development
- 🔄 **API Layer**: Mock endpoints are in place for future game functionality
- 📋 **Phase 2**: Core game mechanics and station environment are planned
- 📋 **Phase 4**: Learning progress analytics and achievements are planned

## Getting Started

### Prerequisites

- Python 3.10+
- Sentence Transformers (for vector embeddings)
- ChromaDB
- FastAPI and Uvicorn (for API server)

Optional for full development:
- Node.js 16+ (for frontend development, when implemented)
- SQLite (for persistent storage, when implemented)

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

The project follows a Test-Driven Development (TDD) approach, with comprehensive test coverage for all components. The tests are organized by module and test type.

### Running Tests

You can run all tests using the provided script:

```bash
cd tests
./run_all_tests.sh
```

Or run specific test categories:

```bash
# Run unit tests for a specific module
python -m pytest tests/backend/ai/companion/core -v

# Run tier1 tests
python -m pytest tests/backend/ai/companion/tier1 -v

# Run tier2 tests
python -m pytest tests/backend/ai/companion/tier2 -v

# Run tier3 tests
python -m pytest tests/backend/ai/companion/tier3 -v

# Run API tests
python -m pytest tests/backend/api -v

# Run DeepSeek parameters test
python -m pytest tests/backend/api/test_deepseek_parameters.py

# Run vector database tests
python -m pytest tests/backend/ai/companion/core/vector/
```

### Integration Tests

The project includes integration tests for different tiers of the AI system:

```bash
# Run tier2 integration tests (Ollama with DeepSeek-R1)
cd tests/backend/integration/tier2
./run_tests.sh

# Run tier3 integration tests (AWS Bedrock)
python -m pytest tests/backend/integration/tier3 -v
```

For more detailed testing information, see the [Testing README](tests/README.md).

### AI Companion Simulator

To test the AI companion functionality without running the full game, you can use the Gradio-based simulator:

```bash
# Install Gradio if you haven't already
pip install gradio httpx python-dotenv

# Run the companion simulator
cd simulator
python app.py
```

The simulator provides a web interface to interact with the AI companion directly. This allows you to:

- Test various conversation patterns and contextual awareness
- Evaluate the effectiveness of topic guardrails
- Test Japanese language responses
- Debug AI behavior in isolation

The simulator provides options to configure different game contexts such as player location, current quest, and request type, giving you control over the testing environment.

For more information, see the [Simulator README](simulator/README.md).

## License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

