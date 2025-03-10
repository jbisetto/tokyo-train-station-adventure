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
