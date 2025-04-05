# NPC Information Endpoint

Endpoint for retrieving general information about a specific NPC in the Tokyo Train Station Adventure game.

**URL:** `/api/npc/{npcId}`

**Method:** `GET`

**Authentication Required:** Yes (via session token)

## Request

```http
GET /api/npc/{npcId}
```

### URL Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `npcId` | string | Unique identifier for the NPC | Yes |

## Response

```json
{
  "npcId": "string",
  "name": "string",
  "role": "string",
  "location": "string",
  "availableDialogueTopics": ["string"],
  "visualAppearance": {
    "spriteKey": "string",
    "animations": ["string"]
  },
  "status": {
    "active": "boolean",
    "currentEmotion": "string",
    "currentActivity": "string"
  }
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `npcId` | string | Unique identifier for the NPC |
| `name` | string | The NPC's display name |
| `role` | string | The NPC's role in the train station |
| `location` | string | The NPC's current location |
| `availableDialogueTopics` | array | List of topics this NPC can discuss |
| `visualAppearance` | object | Visual representation information |
| `visualAppearance.spriteKey` | string | Key for the NPC's sprite sheet |
| `visualAppearance.animations` | array | List of available animations |
| `status` | object | Current state information |
| `status.active` | boolean | Whether the NPC is currently active |
| `status.currentEmotion` | string | Current emotional state |
| `status.currentActivity` | string | Current activity the NPC is engaged in |

## Example Response

```json
{
  "npcId": "ticket_operator",
  "name": "Tanaka",
  "role": "Ticket Machine Operator",
  "location": "ticket_gate_area",
  "availableDialogueTopics": [
    "ticket_purchase",
    "ticket_types",
    "fares",
    "destinations",
    "payment_methods"
  ],
  "visualAppearance": {
    "spriteKey": "ticket_operator_sprite",
    "animations": [
      "idle",
      "talking",
      "pointing",
      "operating_machine",
      "bowing"
    ]
  },
  "status": {
    "active": true,
    "currentEmotion": "neutral",
    "currentActivity": "standing_by_machine"
  }
}
```

## Error Responses

### 400 Bad Request

```json
{
  "error": "Bad Request",
  "message": "Invalid NPC ID format",
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

### 404 Not Found

```json
{
  "error": "Not Found",
  "message": "NPC with ID ticket_operator_2 not found",
  "details": null
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred while retrieving NPC information",
  "details": null
}
```

## Implementation Notes

- This endpoint provides basic information about NPCs that is needed by the game client
- Unlike the NPC Configuration endpoint, this one is accessible to all authenticated users
- The response includes the current state of the NPC, which may change based on game events
- Available dialogue topics influence what conversation options are presented to the player
- Visual appearance information helps the client render the NPC correctly
- Status information can be used to determine if the NPC is currently interactable
- The information returned is a subset of the full NPC configuration, focused on what's needed for gameplay
- This endpoint is typically called when:
  - The player enters an area where NPCs are present
  - The game needs to verify an NPC's status before interaction
  - The UI needs to display information about the NPC
- For more detailed configuration (admin only), use the [Get NPC Configuration](get-npc-config.md) endpoint
