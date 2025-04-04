# Save Game State Endpoint

Endpoint for saving the current game state for a player in the Tokyo Train Station Adventure game.

**URL:** `/api/game/state`

**Method:** `POST`

**Authentication Required:** Yes (via session token)

## Request

```http
POST /api/game/state
Content-Type: application/json
```

### Request Body

```json
{
  "playerId": "string",
  "sessionId": "string",
  "timestamp": "string",
  "location": {
    "area": "string",
    "position": {
      "x": "number",
      "y": "number"
    }
  },
  "questState": {
    "activeQuest": "string",
    "questStep": "string",
    "objectives": [
      {
        "id": "string",
        "completed": "boolean"
      }
    ]
  },
  "inventory": ["string"],
  "gameFlags": {
    "tutorialCompleted": "boolean",
    "metCharacters": ["string"]
  },
  "companions": {
    "hachi": {
      "relationship": "number",
      "assistanceUsed": "number"
    }
  }
}
```

### Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `playerId` | string | Unique identifier for the player | Yes |
| `sessionId` | string | Current session identifier | Yes |
| `timestamp` | string | ISO 8601 formatted timestamp of the save | Yes |
| `location` | object | Player's current location information | Yes |
| `location.area` | string | Named area within the station | Yes |
| `location.position` | object | Precise coordinates within the area | No |
| `location.position.x` | number | X-coordinate | No |
| `location.position.y` | number | Y-coordinate | No |
| `questState` | object | Current quest progress information | Yes |
| `questState.activeQuest` | string | Identifier for the active quest | Yes |
| `questState.questStep` | string | Current step in the active quest | Yes |
| `questState.objectives` | array | List of quest objectives and their status | No |
| `inventory` | array | List of items in player's inventory | No |
| `gameFlags` | object | Various game state flags | No |
| `gameFlags.tutorialCompleted` | boolean | Whether the tutorial has been completed | No |
| `gameFlags.metCharacters` | array | List of characters the player has met | No |
| `companions` | object | Information about companion relationships | No |
| `companions.hachi` | object | State of relationship with Hachi (the dog) | No |

## Response

```json
{
  "success": "boolean",
  "saveId": "string",
  "timestamp": "string"
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the save operation was successful |
| `saveId` | string | Unique identifier for this save state |
| `timestamp` | string | ISO 8601 formatted timestamp of when the save was processed |

## Example Request

```json
{
  "playerId": "player123",
  "sessionId": "session456",
  "timestamp": "2025-03-10T15:30:45Z",
  "location": {
    "area": "ticket_machine_area",
    "position": {
      "x": 320,
      "y": 240
    }
  },
  "questState": {
    "activeQuest": "buy_ticket_to_odawara",
    "questStep": "find_ticket_machine",
    "objectives": [
      {
        "id": "speak_to_information_desk",
        "completed": true
      },
      {
        "id": "locate_ticket_machine",
        "completed": true
      },
      {
        "id": "purchase_ticket",
        "completed": false
      }
    ]
  },
  "inventory": ["station_map", "wallet"],
  "gameFlags": {
    "tutorialCompleted": true,
    "metCharacters": ["info_attendant", "station_guard"]
  },
  "companions": {
    "hachi": {
      "relationship": 0.65,
      "assistanceUsed": 3
    }
  }
}
```

## Example Response

```json
{
  "success": true,
  "saveId": "save_20250310153045_player123",
  "timestamp": "2025-03-10T15:30:47Z"
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

### 403 Forbidden

```json
{
  "error": "Forbidden",
  "message": "Not authorized to save game state for this player",
  "details": null
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred while saving game state",
  "details": null
}
```

## Implementation Notes

- This endpoint integrates with the State Manager component described in the [State Manager Design Document](../docs/design/Tokyo%20Train%20Station%20Adventure%3A%20State%20Manager%20Design%20Document.md)
- The State Manager validates the state changes before persisting them
- Game states are stored in SQLite with Google/Facebook OAuth integration as specified in the [Game Design Document](../docs/design/Tokyo%20Train%20Station%20Adventure%3A%20Language%20Learning%20Game%20Design%20Document.md)
- Auto-save functionality in the game uses this same endpoint with appropriate flags
- Multiple save slots are supported per player, with the `saveId` in the response used for future loading
- The save operation is atomic - either the entire state is saved successfully, or none of it is
