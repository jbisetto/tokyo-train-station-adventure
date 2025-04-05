# Companion Assist Endpoint

Endpoint for requesting assistance from the companion dog (Hachi) in the Tokyo Train Station Adventure game.

**URL:** `/api/companion/assist`

**Method:** `POST`

**Authentication Required:** Yes (via session token)

## Request

```http
POST /api/companion/assist
Content-Type: application/json
```

### Request Body

```json
{
  "playerId": "string",
  "sessionId": "string",
  "gameContext": {
    "location": "string",
    "currentQuest": "string",
    "questStep": "string",
    "nearbyEntities": ["string"],
    "lastInteraction": "string"
  },
  "request": {
    "type": "assistance|vocabulary|grammar|direction|translation",
    "text": "string",
    "targetEntity": "string",
    "targetLocation": "string",
    "language": "english|japanese"
  }
}
```

### Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `playerId` | string | Unique identifier for the player | Yes |
| `sessionId` | string | Current session identifier | Yes |
| `gameContext` | object | Current game state information | Yes |
| `gameContext.location` | string | Player's current location in the station | Yes |
| `gameContext.currentQuest` | string | Active quest identifier | No |
| `gameContext.questStep` | string | Current step in the active quest | No |
| `gameContext.nearbyEntities` | array | List of nearby interactive entities | No |
| `gameContext.lastInteraction` | string | ID of the last entity interacted with | No |
| `request` | object | The assistance request details | Yes |
| `request.type` | string | Type of assistance requested | Yes |
| `request.text` | string | Player's question or request text | No |
| `request.targetEntity` | string | Entity the player is asking about | No |
| `request.targetLocation` | string | Location the player is asking about | No |
| `request.language` | string | Language of the player's request | No |

### Request Type Values

| Type | Description |
|------|-------------|
| `assistance` | General assistance with no specific category |
| `vocabulary` | Help with specific Japanese words or phrases |
| `grammar` | Explanation of grammar patterns |
| `direction` | Guidance navigating the station |
| `translation` | Confirmation of the player's translation |

## Response

```json
{
  "dialogue": {
    "text": "string",
    "japanese": "string|null",
    "pronunciation": "string|null",
    "characterName": "Hachi"
  },
  "companion": {
    "animation": "string",
    "emotionalState": "string",
    "position": {
      "x": "number|null",
      "y": "number|null"
    }
  },
  "ui": {
    "highlights": [
      {
        "id": "string",
        "effect": "pulse|glow|bounce|arrow",
        "duration": "number"
      }
    ],
    "suggestions": [
      {
        "text": "string",
        "action": "string",
        "params": {
          "key": "value"
        }
      }
    ]
  },
  "gameState": {
    "learningMoments": ["string"],
    "questProgress": "string|null",
    "vocabularyUnlocked": ["string"]
  },
  "meta": {
    "responseId": "string",
    "processingTier": "rule|local|cloud"
  }
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `dialogue` | object | The companion's response text |
| `dialogue.text` | string | The main dialogue text (in English) |
| `dialogue.japanese` | string | Japanese text if relevant, null otherwise |
| `dialogue.pronunciation` | string | Romanized pronunciation if relevant, null otherwise |
| `dialogue.characterName` | string | Always "Hachi" for the companion dog |
| `companion` | object | Animation and state information for the companion |
| `companion.animation` | string | Animation to play (e.g., "pointing", "tail_wag", "sitting") |
| `companion.emotionalState` | string | Emotional state (e.g., "excited", "thoughtful", "curious") |
| `companion.position` | object | Optional positioning information |
| `ui` | object | UI-related elements triggered by the response |
| `ui.highlights` | array | Elements in the game to highlight for the player |
| `ui.suggestions` | array | Suggested follow-up actions or questions |
| `gameState` | object | Game state updates from this interaction |
| `gameState.learningMoments` | array | Language learning opportunities identified |
| `gameState.questProgress` | string | Quest progress update if relevant, null otherwise |
| `gameState.vocabularyUnlocked` | array | New vocabulary items unlocked |
| `meta` | object | Metadata about the response |
| `meta.responseId` | string | Unique identifier for this response |
| `meta.processingTier` | string | AI tier that processed the request (rule-based, local LLM, or cloud) |

## Example Request

```json
{
  "playerId": "player123",
  "sessionId": "session456",
  "gameContext": {
    "location": "ticket_machine_area",
    "currentQuest": "buy_ticket_to_odawara",
    "questStep": "find_ticket_machine",
    "nearbyEntities": ["ticket_machine_1", "station_map", "information_booth"],
    "lastInteraction": "station_map"
  },
  "request": {
    "type": "vocabulary",
    "text": "What does 切符 mean?",
    "targetEntity": "ticket_machine_1",
    "language": "english"
  }
}
```

## Example Response

```json
{
  "dialogue": {
    "text": "Woof! 切符 (kippu) means 'ticket' in Japanese. You'll need this word when buying your ticket to Odawara. It's an important word at the train station!",
    "japanese": "切符",
    "pronunciation": "kippu",
    "characterName": "Hachi"
  },
  "companion": {
    "animation": "tail_wag",
    "emotionalState": "helpful",
    "position": {
      "x": null,
      "y": null
    }
  },
  "ui": {
    "highlights": [
      {
        "id": "ticket_machine_1",
        "effect": "pulse",
        "duration": 3000
      }
    ],
    "suggestions": [
      {
        "text": "How do I buy a ticket?",
        "action": "ASK_QUESTION",
        "params": {
          "topic": "ticket_purchase"
        }
      },
      {
        "text": "What is 'platform' in Japanese?",
        "action": "VOCABULARY_QUESTION",
        "params": {
          "word": "platform"
        }
      }
    ]
  },
  "gameState": {
    "learningMoments": ["vocabulary_ticket"],
    "questProgress": null,
    "vocabularyUnlocked": ["切符"]
  },
  "meta": {
    "responseId": "resp789",
    "processingTier": "rule"
  }
}
```

## Error Responses

### 400 Bad Request

```json
{
  "error": "Bad Request",
  "message": "Invalid request format or missing required fields",
  "details": {
    "fieldErrors": [
      {
        "field": "playerId",
        "message": "Field is required"
      }
    ]
  }
}
```

### 401 Unauthorized

```json
{
  "error": "Unauthorized",
  "message": "Authentication required to access this endpoint",
  "details": null
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred while processing the request",
  "details": null
}
```

## Implementation Notes

- This endpoint uses the Companion AI system described in the [Companion AI Design Document](../docs/ai/Tokyo%20Train%20Station%20Adventure%3A%20Companion%20AI%20Design%20Document.md)
- Response processing follows the tiered approach (70% rule-based, 20% local LLM, 10% cloud) outlined in the [AI Implementation Plan](../docs/ai/Tokyo%20Train%20Station%20Adventure%20-%20AI%20Implementation%20Plan.md)
- The response is transformed through the adapter layer as detailed in the [API Design Document](adapter-design.md)
