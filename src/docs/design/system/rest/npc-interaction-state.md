# NPC Interaction State Endpoint

Endpoint for retrieving the current state of interaction between a player and a specific NPC in the Tokyo Train Station Adventure game.

**URL:** `/api/npc/state/{playerId}/{npcId}`

**Method:** `GET`

**Authentication Required:** Yes (via session token)

## Request

```http
GET /api/npc/state/{playerId}/{npcId}
```

### URL Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `playerId` | string | Unique identifier for the player | Yes |
| `npcId` | string | Unique identifier for the NPC | Yes |

## Response

```json
{
  "playerId": "string",
  "npcId": "string",
  "relationshipMetrics": {
    "familiarityLevel": "number",
    "interactionCount": "number",
    "lastInteractionTime": "string"
  },
  "conversationState": {
    "activeConversation": "boolean",
    "conversationId": "string|null",
    "turnCount": "number",
    "pendingResponse": "boolean"
  },
  "gameProgressUnlocks": {
    "unlockedTopics": ["string"],
    "completedInteractions": ["string"],
    "availableQuests": ["string"]
  }
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `playerId` | string | Unique identifier for the player |
| `npcId` | string | Unique identifier for the NPC |
| `relationshipMetrics` | object | Metrics tracking the player-NPC relationship |
| `relationshipMetrics.familiarityLevel` | number | How familiar the player is with the NPC (0.0-1.0) |
| `relationshipMetrics.interactionCount` | number | How many times the player has interacted with this NPC |
| `relationshipMetrics.lastInteractionTime` | string | ISO 8601 timestamp of the last interaction |
| `conversationState` | object | Current conversation state information |
| `conversationState.activeConversation` | boolean | Whether there is an active conversation |
| `conversationState.conversationId` | string | ID of the active conversation, if any |
| `conversationState.turnCount` | number | Number of turns in the current conversation |
| `conversationState.pendingResponse` | boolean | Whether the NPC is waiting for a player response |
| `gameProgressUnlocks` | object | Progress-related information |
| `gameProgressUnlocks.unlockedTopics` | array | Dialogue topics unlocked with this NPC |
| `gameProgressUnlocks.completedInteractions` | array | Key interactions completed with this NPC |
| `gameProgressUnlocks.availableQuests` | array | Quests available from this NPC based on progress |

## Example Response

```json
{
  "playerId": "player123",
  "npcId": "ticket_operator",
  "relationshipMetrics": {
    "familiarityLevel": 0.45,
    "interactionCount": 3,
    "lastInteractionTime": "2025-03-10T14:32:17Z"
  },
  "conversationState": {
    "activeConversation": true,
    "conversationId": "conv_20250310143217_ticket_operator",
    "turnCount": 4,
    "pendingResponse": true
  },
  "gameProgressUnlocks": {
    "unlockedTopics": [
      "ticket_purchase",
      "station_layout",
      "train_schedules"
    ],
    "completedInteractions": [
      "initial_greeting",
      "ticket_inquiry"
    ],
    "availableQuests": [
      "find_platform_for_odawara"
    ]
  }
}
```

## Error Responses

### 400 Bad Request

```json
{
  "error": "Bad Request",
  "message": "Invalid player ID or NPC ID format",
  "details": null
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

### 403 Forbidden

```json
{
  "error": "Forbidden",
  "message": "Not authorized to access interaction state for this player",
  "details": null
}
```

### 404 Not Found

```json
{
  "error": "Not Found",
  "message": "No interaction state found for this player-NPC combination",
  "details": null
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred while retrieving interaction state",
  "details": null
}
```

## Implementation Notes

- This endpoint provides information about the specific relationship between a player and an NPC
- The relationship data influences dialogue options and NPC behaviors toward the player
- Conversation state information can be used to:
  - Resume interrupted conversations
  - Track dialogue progress
  - Determine if the player needs to respond
- The game progress unlocks section indicates what content has been made available through interactions
- The familiarity level affects how the NPC addresses the player and what information they share
- The interaction state is maintained separately from the NPC configuration and general information
- This endpoint is typically called:
  - When a player approaches an NPC to determine available interactions
  - Before starting a new conversation to check for pending conversations
  - When loading a saved game to restore NPC relationship states
- The data is updated automatically after each interaction with the NPC via the [NPC Dialogue](npc-dialogue.md) endpoint
- Interaction state persists between game sessions and is part of the overall game state
