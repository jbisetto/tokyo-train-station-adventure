# NPC Dialogue Endpoint

Endpoint for processing dialogue interactions between the player and NPCs in the Tokyo Train Station Adventure game.

**URL:** `/api/npc/dialogue`

**Method:** `POST`

**Authentication Required:** Yes (via session token)

## Request

```http
POST /api/npc/dialogue
Content-Type: application/json
```

### Request Body

```json
{
  "playerContext": {
    "playerId": "string",
    "sessionId": "string",
    "languageLevel": "string",
    "learningProgress": {
      "vocabularyMastered": "integer",
      "grammarPoints": "integer",
      "conversationSuccess": "number"
    }
  },
  "gameContext": {
    "location": "string",
    "currentQuest": "string",
    "questStep": "string",
    "interactionHistory": [
      {
        "npcId": "string",
        "completed": "boolean"
      }
    ],
    "timeOfDay": "string",
    "gameFlags": {
      "key": "boolean"
    }
  },
  "npcId": "string",
  "playerInput": {
    "text": "string",
    "inputType": "keyboard|multiple_choice",
    "language": "japanese|english",
    "selectedOptionId": "string|null"
  },
  "conversationContext": {
    "conversationId": "string|null",
    "previousExchanges": [
      {
        "speaker": "player|npc",
        "text": "string",
        "timestamp": "string"
      }
    ]
  }
}
```

### Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `playerContext` | object | Information about the player | Yes |
| `playerContext.playerId` | string | Unique identifier for the player | Yes |
| `playerContext.sessionId` | string | Current session identifier | Yes |
| `playerContext.languageLevel` | string | JLPT level of the player (N5, N4, etc.) | No |
| `playerContext.learningProgress` | object | Summary of player's language progress | No |
| `gameContext` | object | Current game state information | Yes |
| `gameContext.location` | string | Player's current location in the station | Yes |
| `gameContext.currentQuest` | string | Active quest identifier | No |
| `gameContext.questStep` | string | Current step in the active quest | No |
| `gameContext.interactionHistory` | array | Previous NPC interactions | No |
| `gameContext.timeOfDay` | string | Current game time period | No |
| `gameContext.gameFlags` | object | Various game state flags | No |
| `npcId` | string | Identifier for the NPC being addressed | Yes |
| `playerInput` | object | The player's dialogue input | Yes |
| `playerInput.text` | string | Player's text input | Yes |
| `playerInput.inputType` | string | Method of input used | Yes |
| `playerInput.language` | string | Language of the player's input | Yes |
| `playerInput.selectedOptionId` | string | ID of selected option (for multiple-choice) | No |
| `conversationContext` | object | Information about the ongoing conversation | No |
| `conversationContext.conversationId` | string | ID of an ongoing conversation, null if new | No |
| `conversationContext.previousExchanges` | array | Record of previous exchanges | No |

## Response

```json
{
  "conversationId": "string",
  "npcResponse": {
    "text": "string",
    "japanese": "string|null",
    "pronunciation": "string|null",
    "animation": "string",
    "emotion": "string"
  },
  "feedback": {
    "correctness": "number",
    "corrections": [
      {
        "original": "string",
        "corrected": "string",
        "explanation": "string"
      }
    ]
  },
  "expectedInput": {
    "type": "open|multiple_choice|none",
    "options": [
      {
        "id": "string",
        "text": "string"
      }
    ]
  },
  "gameStateChanges": {
    "questProgress": "boolean",
    "newObjective": "string|null",
    "learningMoments": ["string"]
  },
  "meta": {
    "confidence": "number",
    "responseTime": "number",
    "promptTokens": "number",
    "completionTokens": "number"
  }
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `conversationId` | string | Identifier for this conversation (for continuation) |
| `npcResponse` | object | The NPC's response |
| `npcResponse.text` | string | The main response text (in English) |
| `npcResponse.japanese` | string | Japanese text if relevant, null otherwise |
| `npcResponse.pronunciation` | string | Romanized pronunciation if relevant |
| `npcResponse.animation` | string | Animation to play for the NPC |
| `npcResponse.emotion` | string | Emotional state to display (e.g., "happy", "confused") |
| `feedback` | object | Feedback on the player's Japanese language usage |
| `feedback.correctness` | number | Score from 0.0-1.0 indicating correctness |
| `feedback.corrections` | array | Specific corrections to the player's input |
| `expectedInput` | object | What type of input is expected next |
| `expectedInput.type` | string | Whether open input, multiple choice, or no input is expected |
| `expectedInput.options` | array | Options if multiple-choice input is expected |
| `gameStateChanges` | object | Changes to game state from this interaction |
| `gameStateChanges.questProgress` | boolean | Whether quest progress was made |
| `gameStateChanges.newObjective` | string | New objective if quest updated |
| `gameStateChanges.learningMoments` | array | Language learning opportunities |
| `meta` | object | Metadata about the response |
| `meta.confidence` | number | AI confidence in the response (0.0-1.0) |
| `meta.responseTime` | number | Processing time in milliseconds |
| `meta.promptTokens` | number | Number of tokens in the prompt |
| `meta.completionTokens` | number | Number of tokens in the completion |

## Example Request

```json
{
  "playerContext": {
    "playerId": "player123",
    "sessionId": "session456",
    "languageLevel": "N5",
    "learningProgress": {
      "vocabularyMastered": 42,
      "grammarPoints": 11,
      "conversationSuccess": 0.82
    }
  },
  "gameContext": {
    "location": "ticket_machine_area",
    "currentQuest": "buy_ticket_to_odawara",
    "questStep": "find_ticket_machine",
    "interactionHistory": [
      {
        "npcId": "info_attendant",
        "completed": true
      }
    ],
    "timeOfDay": "morning",
    "gameFlags": {
      "tutorialCompleted": true
    }
  },
  "npcId": "ticket_operator",
  "playerInput": {
    "text": "小田原までの切符をください。",
    "inputType": "keyboard",
    "language": "japanese",
    "selectedOptionId": null
  },
  "conversationContext": {
    "conversationId": null,
    "previousExchanges": []
  }
}
```

## Example Response

```json
{
  "conversationId": "conv_20250310162145_ticket_operator",
  "npcResponse": {
    "text": "One ticket to Odawara? Certainly. That will be 1,500 yen. Will this be one-way or round-trip?",
    "japanese": "小田原までの切符ですね。はい、1,500円です。片道ですか、往復ですか？",
    "pronunciation": "Odawara made no kippu desu ne. Hai, sen-gohyaku-en desu. Katamichi desu ka, ōfuku desu ka?",
    "animation": "operating_machine",
    "emotion": "helpful"
  },
  "feedback": {
    "correctness": 0.95,
    "corrections": []
  },
  "expectedInput": {
    "type": "multiple_choice",
    "options": [
      {
        "id": "opt1",
        "text": "片道です。"
      },
      {
        "id": "opt2",
        "text": "往復でお願いします。"
      }
    ]
  },
  "gameStateChanges": {
    "questProgress": true,
    "newObjective": "purchase_ticket",
    "learningMoments": ["travel_vocabulary", "ticket_purchase_dialogue"]
  },
  "meta": {
    "confidence": 0.98,
    "responseTime": 345,
    "promptTokens": 412,
    "completionTokens": 89
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
        "field": "npcId",
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

### 404 Not Found

```json
{
  "error": "Not Found",
  "message": "NPC with ID ticket_operator_2 not found",
  "details": null
}
```

### 422 Unprocessable Entity

```json
{
  "error": "Unprocessable Entity",
  "message": "Unable to process dialogue input",
  "details": {
    "reason": "Language not supported"
  }
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred while processing the dialogue",
  "details": null
}
```

## Implementation Notes

- This endpoint integrates with the NPC AI system described in the [NPC AI Architecture](../docs/ai/Tokyo%20Train%20Station%20Adventure%3A%20NPC%20AI%20Architecture.md) document
- NPC responses are generated using the tiered AI approach:
  - 70% rule-based responses for common interactions
  - 20% local DeepSeek 7B model for moderately complex responses
  - 10% cloud API for novel or complex interactions
- NPC behaviors are determined by their configuration (see [NPC AI API Specification](../docs/ai/Tokyo%20Train%20Station%20Adventure%3A%20NPC%20AI%20API%20Specification.md))
- Language feedback is tailored to the player's JLPT level
- The response includes game state changes that should be applied by the client
- Metadata provides insights into the AI processing for monitoring and optimization
- The Dialogue Manager routes this endpoint to the appropriate NPC instance as described in the [Dialogue Manager Design Document](../docs/design/Tokyo%20Train%20Station%20Adventure%3A%20Dialogue%20Manager%20Design%20Document.md)
