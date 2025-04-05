# Tokyo Train Station Adventure
## REST API Documentation

This repository contains the API specification for the Tokyo Train Station Adventure language learning game. The API provides a communication interface between the Phaser.js game frontend and the Python backend.

## API Overview

The API uses a RESTful design with JSON for data exchange. All endpoints return consistent error structures and follow standard HTTP status codes.

## Endpoint Categories

### Companion Assistance
| Endpoint | Method | Description | Documentation |
|----------|--------|-------------|---------------|
| `/api/companion/assist` | POST | Request assistance from the companion dog | [Companion Assist](companion-assist.md) |

### Dialogue Processing
| Endpoint | Method | Description | Documentation |
|----------|--------|-------------|---------------|
| `/api/dialogue/process` | POST | Process dialogue between the player and NPCs/companion | [Dialogue Process](dialogue-process.md) |

### Player Progress
| Endpoint | Method | Description | Documentation |
|----------|--------|-------------|---------------|
| `/api/player/progress/{playerId}` | GET | Retrieve the player's Japanese language learning progress | [Player Progress](player-progress.md) |

### Game State
| Endpoint | Method | Description | Documentation |
|----------|--------|-------------|---------------|
| `/api/game/state` | POST | Save the current game state | [Save Game State](save-game-state.md) |
| `/api/game/state/{playerId}` | GET | Load a saved game state | [Load Game State](load-game-state.md) |

### NPC Information
| Endpoint | Method | Description | Documentation |
|----------|--------|-------------|---------------|
| `/api/npc/dialogue` | POST | Process dialogue with an NPC | [NPC Dialogue](npc-dialogue.md) |
| `/api/npc/config/{npcId}` | GET | Retrieve the configuration for a specific NPC | [Get NPC Config](get-npc-config.md) |
| `/api/npc/config/{npcId}` | PUT | Update the configuration for a specific NPC | [Update NPC Config](update-npc-config.md) |
| `/api/npc/{npcId}` | GET | Get information about a specific NPC | [NPC Information](npc-information.md) |
| `/api/npc/state/{playerId}/{npcId}` | GET | Get the current state of interaction between a player and an NPC | [NPC Interaction State](npc-interaction-state.md) |
| `/api/npc/engine/parameters` | POST | Adjust parameters for the DeepSeek engine (admin endpoint) | [DeepSeek Parameters](deepseek-parameters.md) |

## Technical Design

For detailed information about the API implementation, refer to the following documents:

1. [Adapter Design](adapter-design.md) - Information about how the API transforms backend responses for frontend use
2. [Error Handling](error-handling.md) - Details on API error responses and handling
3. [Security Considerations](security-considerations.md) - Information about authentication and other security measures

## Integration Reference

To understand how the API integrates with the game's components, refer to:

- [Tokyo Train Station Adventure - Python Game Logic Architecture.md](../docs/design/Tokyo%20Train%20Station%20Adventure%20-%20Python%20Game%20Logic%20Architecture.md)
- [Tokyo Train Station Adventure - AI Implementation Plan.md](../docs/ai/Tokyo%20Train%20Station%20Adventure%20-%20AI%20Implementation%20Plan.md)
- [Tokyo Train Station Adventure: UI and AI Integration.md](../docs/ui/Tokyo%20Train%20Station%20Adventure%3A%20UI%20and%20AI%20Integration.md)

## Implementation Status

This API specification is currently in the planning phase. Implementation will begin once the core game architecture is established.
