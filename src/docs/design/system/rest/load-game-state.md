# Load Game State Endpoint

Endpoint for loading a saved game state for a player in the Tokyo Train Station Adventure game.

**URL:** `/api/game/state/{playerId}`

**Method:** `GET`

**Authentication Required:** Yes (via session token)

## Request

```http
GET /api/game/state/{playerId}
```

### URL Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `playerId` | string | Unique identifier for the player | Yes |

### Query Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `saveId` | string | Specific save ID to load (if not provided, loads the most recent save) | No |
| `sessionId` | string | Current session identifier | Yes |

## Response

```json
{
  "playerId": "string",
  "lastPlayed": "string",
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
        "completed": "boolean",
        "description": "string"
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

| Field | Type | Description |
|-------|------|-------------|
| `playerId` | string | Unique identifier for the player |
| `lastPlayed` | string | ISO 8601 formatted timestamp of when the save was created |
| `location` | object | Player's saved location information |
| `location.area` | string | Named area within the station |
| `location.position` | object | Precise coordinates within the area |
| `location.position.x` | number | X-coordinate |
| `location.position.y` | number | Y-coordinate |
| `questState` | object | Saved quest progress information |
| `questState.activeQuest` | string | Identifier for the active quest |
| `questState.questStep` | string | Current step in the active quest |
| `questState.objectives` | array | List of quest objectives and their status |
| `questState.objectives[].id` | string | Objective identifier |
| `questState.objectives[].completed` | boolean | Whether the objective is completed |
| `questState.objectives[].description` | string | Human-readable description of the objective |
| `inventory` | array | List of items in player's inventory |
| `gameFlags` | object | Various game state flags |
| `gameFlags.tutorialCompleted` | boolean | Whether the tutorial has been completed |
| `gameFlags.metCharacters` | array | List of characters the player has met |
| `companions` | object | Information about companion relationships |
| `companions.hachi` | object | State of relationship with Hachi (the dog) |
| `companions.hachi.relationship` | number | Relationship level with Hachi (0.0-1.0) |
| `companions.hachi.assistanceUsed` | number | Number of times assistance was used |

## Example Response

```json
{
  "playerId": "player123",
  "lastPlayed": "2025-03-10T15:30:45Z",
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
        "completed": true,
        "description": "Speak to the information desk attendant"
      },
      {
        "id": "locate_ticket_machine",
        "completed": true,
        "description": "Find a ticket machine"
      },
      {
        "id": "purchase_ticket",
        "completed": false,
        "description": "Purchase a ticket to Odawara"
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

## List Saved Games

To retrieve a list of available saved games for a player:

```http
GET /api/game/saves/{playerId}
```

### Response

```json
{
  "playerId": "string",
  "saves": [
    {
      "saveId": "string",
      "timestamp": "string",
      "location": "string",
      "questName": "string",
      "level": "string"
    }
  ]
}
```

## Error Responses

### 400 Bad Request

```json
{
  "error": "Bad Request",
  "message": "Invalid player ID format",
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
  "message": "Not authorized to load game state for this player",
  "details": null
}
```

### 404 Not Found

```json
{
  "error": "Not Found",
  "message": "No saved game found for player",
  "details": null
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred while loading game state",
  "details": null
}
```

## Implementation Notes

- This endpoint integrates with the State Manager component described in the [State Manager Design Document](../docs/design/Tokyo%20Train%20Station%20Adventure%3A%20State%20Manager%20Design%20Document.md)
- The loaded state is automatically validated for consistency before being returned
- Game states are retrieved from SQLite storage with appropriate authentication checks
- If a specific `saveId` is not provided, the most recent save will be loaded
- The response includes all information needed to restore the game to the saved state
- This endpoint can be used in conjunction with the "Continue Game" option from the main menu
- Learning progress data is stored separately and retrieved via the [Player Progress API](player-progress.md)
