# Dialogue Process Endpoint

Endpoint for processing dialogue exchanges between the player and NPCs or the companion in the Tokyo Train Station Adventure game.

**URL:** `/api/dialogue/process`

**Method:** `POST`

**Authentication Required:** Yes (via session token)

## Request

```http
POST /api/dialogue/process
Content-Type: application/json
```

### Request Body

```json
{
  "playerId": "string",
  "sessionId": "string",
  "conversationId": "string|null",
  "speakerId": "string",
  "speakerType": "companion|npc|player",
  "gameContext": {
    "location": "string",
    "currentQuest": "string",
    "questStep": "string"
  },
  "dialogueInput": {
    "text": "string",
    "inputType": "keyboard|multiple_choice|voice",
    "language": "english|japanese",
    "selectedOptionId": "string|null"
  },
  "previousExchanges": [
    {
      "speaker": "string",
      "text": "string",
      "timestamp": "string"
    }
  ]
}
```

### Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `playerId` | string | Unique identifier for the player | Yes |
| `sessionId` | string | Current session identifier | Yes |
| `conversationId` | string | Identifier for an ongoing conversation, null if new | No |
| `speakerId` | string | ID of the entity being spoken to | Yes |
| `speakerType` | string | Type of entity being spoken to | Yes |
| `gameContext` | object | Current game state information | Yes |
| `gameContext.location` | string | Player's current location in the station | Yes |
| `gameContext.currentQuest` | string | Active quest identifier | No |
| `gameContext.questStep` | string | Current step in the active quest | No |
| `dialogueInput` | object | The player's dialogue input | Yes |
| `dialogueInput.text` | string | Player's text input | Yes |
| `dialogueInput.inputType` | string | Method of input used | Yes |
| `dialogueInput.language` | string | Language of the player's input | Yes |
| `dialogueInput.selectedOptionId` | string | ID of selected multiple-choice option, if applicable | No |
| `previousExchanges` | array | Prior exchanges in the current conversation | No |

### Speaker Type Values

| Type | Description |
|------|-------------|
| `companion` | The companion dog (Hachi) |
| `npc` | A non-player character |
| `player` | The player (usually for reference only) |

### Input Type Values

| Type | Description |
|------|-------------|
| `keyboard` | Free text input via keyboard |
| `multiple_choice` | Selection from predefined options |
| `voice` | Voice input (future capability) |

## Response

```json
{
  "dialogue": {
    "text": "string",
    "japanese": "string|null",
    "pronunciation": "string|null",
    "characterName": "string",
    "audioUrl": "string|null"
  },
  "feedback": {
    "correctness": "number",
    "message": "string|null",
    "corrections": [
      {
        "original": "string",
        "corrected": "string",
        "explanation": "string",
        "position": {
          "start": "number",
          "end": "number"
        }
      }
    ],
    "highlightColor": "string|null"
  },
  "npc": {
    "id": "string|null",
    "animation": "string|null",
    "emotionalState": "string|null"
  },
  "companion": {
    "animation": "string|null",
    "emotionalState": "string|null",
    "hasHint": "boolean"
  },
  "ui": {
    "inputType": "open|multiple_choice|none",
    "options": [
      {
        "id": "string",
        "text": "string"
      }
    ],
    "suggestions": [
      {
        "text": "string",
        "action": "string",
        "params": {}
      }
    ]
  },
  "gameState": {
    "conversationId": "string",
    "questUpdated": "boolean",
    "newObjective": "string|null",
    "learningMoments": ["string"],
    "completedExchange": "boolean"
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
| `dialogue` | object | The response dialogue content |
| `dialogue.text` | string | The main dialogue text (in English) |
| `dialogue.japanese` | string | Japanese text if relevant, null otherwise |
| `dialogue.pronunciation` | string | Romanized pronunciation if relevant, null otherwise |
| `dialogue.characterName` | string | Name of the speaking character |
| `dialogue.audioUrl` | string | URL to audio file of spoken dialogue, if available |
| `feedback` | object | Feedback on the player's Japanese language usage |
| `feedback.correctness` | number | Score from 0.0-1.0 indicating correctness |
| `feedback.message` | string | Optional feedback message on language usage |
| `feedback.corrections` | array | Specific corrections to the player's input |
| `feedback.highlightColor` | string | CSS color for highlighting based on correctness |
| `npc` | object | Information about the NPC's state (if applicable) |
| `npc.id` | string | ID of the speaking NPC, null if not an NPC |
| `npc.animation` | string | Animation to play for the NPC |
| `npc.emotionalState` | string | Emotional state of the NPC |
| `companion` | object | Information about companion's state during this exchange |
| `companion.animation` | string | Animation to play for companion |
| `companion.emotionalState` | string | Emotional state of companion |
| `companion.hasHint` | boolean | Whether the companion has a hint available |
| `ui` | object | UI-related elements for the response |
| `ui.inputType` | string | Type of input expected for the next exchange |
| `ui.options` | array | Options if multiple-choice input is expected |
| `ui.suggestions` | array | Suggested responses or actions |
| `gameState` | object | Game state updates from this interaction |
| `gameState.conversationId` | string | ID of the conversation (new or existing) |
| `gameState.questUpdated` | boolean | Whether this exchange updated quest progress |
| `gameState.newObjective` | string | New objective if quest updated, null otherwise |
| `gameState.learningMoments` | array | Language learning opportunities identified |
| `gameState.completedExchange` | boolean | Whether this exchange completes a conversation |
| `meta` | object | Metadata about the response |
| `meta.responseId` | string | Unique identifier for this response |
| `meta.processingTier` | string | AI tier that processed the request |

## Example Request

```json
{
  "playerId": "player123",
  "sessionId": "session456",
  "conversationId": "conv789",
  "speakerId": "info_attendant",
  "speakerType": "npc",
  "gameContext": {
    "location": "information_booth",
    "currentQuest": "buy_ticket_to_odawara",
    "questStep": "ask_for_directions"
  },
  "dialogueInput": {
    "text": "おだわらに行きたいです。",
    "inputType": "keyboard",
    "language": "japanese",
    "selectedOptionId": null
  },
  "previousExchanges": [
    {
      "speaker": "info_attendant",
      "text": "いらっしゃいませ。何かお手伝いできますか？",
      "timestamp": "2025-03-10T14:22:30Z"
    }
  ]
}
```

## Example Response

```json
{
  "dialogue": {
    "text": "Oh, you want to go to Odawara? You'll need to buy a ticket first. The ticket machines are over there.",
    "japanese": "小田原に行きたいですね。まず切符を買う必要があります。券売機はあそこです。",
    "pronunciation": "Odawara ni ikitai desu ne. Mazu kippu o kau hitsuyō ga arimasu. Kenbaiki wa asoko desu.",
    "characterName": "Information Attendant",
    "audioUrl": "/audio/npc/info_attendant/response_odawara.mp3"
  },
  "feedback": {
    "correctness": 0.95,
    "message": "Excellent Japanese! Your sentence was clear and correct.",
    "corrections": [],
    "highlightColor": "#06D6A0"
  },
  "npc": {
    "id": "info_attendant",
    "animation": "pointing",
    "emotionalState": "helpful"
  },
  "companion": {
    "animation": "tail_wag",
    "emotionalState": "excited",
    "hasHint": false
  },
  "ui": {
    "inputType": "multiple_choice",
    "options": [
      {
        "id": "opt1",
        "text": "切符はいくらですか？"
      },
      {
        "id": "opt2",
        "text": "どうもありがとうございます。"
      },
      {
        "id": "opt3",
        "text": "券売機はどこですか？"
      }
    ],
    "suggestions": []
  },
  "gameState": {
    "conversationId": "conv789",
    "questUpdated": true,
    "newObjective": "find_ticket_machine",
    "learningMoments": ["destination_vocabulary", "polite_request_form"],
    "completedExchange": false
  },
  "meta": {
    "responseId": "resp123",
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
        "field": "dialogueInput.text",
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
  "message": "Specified speakerId not found",
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

- This endpoint integrates with both the NPC AI system and Companion AI system as described in the [NPC AI Architecture](../docs/ai/Tokyo%20Train%20Station%20Adventure%3A%20NPC%20AI%20Architecture.md) and [Companion AI Design Document](../docs/ai/Tokyo%20Train%20Station%20Adventure%3A%20Companion%20AI%20Design%20Document.md)
- The Dialogue Manager handles routing to the appropriate AI system based on the `speakerType` parameter
- Response processing follows the tiered approach (70% rule-based, 20% local LLM, 10% cloud) outlined in the [AI Implementation Plan](../docs/ai/Tokyo%20Train%20Station%20Adventure%20-%20AI%20Implementation%20Plan.md)
- The response is transformed through the adapter layer as detailed in the [API Design Document](adapter-design.md)
- Detailed architecture is described in the [Dialogue Manager Design Document](../docs/design/Tokyo%20Train%20Station%20Adventure%3A%20Dialogue%20Manager%20Design%20Document.md)
