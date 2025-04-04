# DeepSeek Parameters Endpoint

Endpoint for adjusting parameters for the DeepSeek AI engine used by NPCs in the Tokyo Train Station Adventure game.

**URL:** `/api/npc/engine/parameters`

**Method:** `POST`

**Authentication Required:** Yes (via session token)

**Role Required:** Admin (standard players cannot adjust AI engine parameters)

## Request

```http
POST /api/npc/engine/parameters
Content-Type: application/json
```

### Request Body

```json
{
  "globalParameters": {
    "temperature": "number|null",
    "topP": "number|null",
    "frequencyPenalty": "number|null",
    "presencePenalty": "number|null",
    "maxTokens": "number|null"
  },
  "npcSpecificOverrides": [
    {
      "npcId": "string",
      "parameters": {
        "temperature": "number|null",
        "topP": "number|null",
        "frequencyPenalty": "number|null",
        "presencePenalty": "number|null",
        "maxTokens": "number|null"
      }
    }
  ],
  "contextWindowSettings": {
    "maxHistoryTurns": "number|null",
    "maxPromptTokens": "number|null",
    "reservedTokens": "number|null"
  },
  "applyImmediately": "boolean"
}
```

### Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `globalParameters` | object | Parameters that apply to all NPCs | No |
| `globalParameters.temperature` | number | Control randomness (0.0-1.0) | No |
| `globalParameters.topP` | number | Nucleus sampling parameter (0.0-1.0) | No |
| `globalParameters.frequencyPenalty` | number | Penalty for token frequency (0.0-2.0) | No |
| `globalParameters.presencePenalty` | number | Penalty for token presence (0.0-2.0) | No |
| `globalParameters.maxTokens` | number | Max tokens to generate per response | No |
| `npcSpecificOverrides` | array | Parameter overrides for specific NPCs | No |
| `npcSpecificOverrides[].npcId` | string | ID of the NPC to override parameters for | Yes (in array) |
| `npcSpecificOverrides[].parameters` | object | Parameter overrides for this NPC | Yes (in array) |
| `contextWindowSettings` | object | Settings for context window management | No |
| `contextWindowSettings.maxHistoryTurns` | number | Maximum conversation turns to include | No |
| `contextWindowSettings.maxPromptTokens` | number | Maximum tokens in prompt | No |
| `contextWindowSettings.reservedTokens` | number | Tokens reserved for response | No |
| `applyImmediately` | boolean | Whether to apply changes to ongoing conversations | Yes |

Note: For each parameter, providing `null` will revert the parameter to its default value. All parameter fields are optional.

## Response

```json
{
  "success": "boolean",
  "message": "string",
  "appliedSettings": {
    "global": {},
    "npcSpecific": {}
  },
  "effectiveTime": "string"
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the operation was successful |
| `message` | string | A message describing the result of the operation |
| `appliedSettings` | object | Summary of settings that were applied |
| `appliedSettings.global` | object | Global parameters that were set |
| `appliedSettings.npcSpecific` | object | NPC-specific parameters that were set |
| `effectiveTime` | string | ISO 8601 timestamp of when settings become effective |

## Example Request

```json
{
  "globalParameters": {
    "temperature": 0.65,
    "maxTokens": 250
  },
  "npcSpecificOverrides": [
    {
      "npcId": "info_attendant",
      "parameters": {
        "temperature": 0.8,
        "frequencyPenalty": 1.2
      }
    },
    {
      "npcId": "ticket_operator",
      "parameters": {
        "temperature": 0.5,
        "maxTokens": 150
      }
    }
  ],
  "contextWindowSettings": {
    "maxHistoryTurns": 5,
    "reservedTokens": 300
  },
  "applyImmediately": false
}
```

## Example Response

```json
{
  "success": true,
  "message": "DeepSeek parameters updated successfully",
  "appliedSettings": {
    "global": {
      "temperature": 0.65,
      "maxTokens": 250
    },
    "npcSpecific": {
      "info_attendant": {
        "temperature": 0.8,
        "frequencyPenalty": 1.2
      },
      "ticket_operator": {
        "temperature": 0.5,
        "maxTokens": 150
      }
    }
  },
  "effectiveTime": "2025-03-12T10:15:30Z"
}
```

## Parameter Effects

| Parameter | Description | Effect on Dialogue |
|-----------|-------------|-------------------|
| `temperature` | Controls randomness | Higher values make responses more creative and varied; lower values make responses more deterministic and focused |
| `topP` | Nucleus sampling | Limits token selection to those that make up a cumulative probability; lower values create more focused responses |
| `frequencyPenalty` | Penalizes frequent tokens | Higher values reduce repetition of phrases and patterns |
| `presencePenalty` | Penalizes tokens used at all | Higher values encourage exploration of new topics and vocabulary |
| `maxTokens` | Limits response length | Controls the maximum response length in tokens |
| `maxHistoryTurns` | Conversation history | Controls how many previous exchanges are included for context |
| `maxPromptTokens` | Prompt token limit | Limits the size of the entire prompt sent to DeepSeek |
| `reservedTokens` | Response space | Reserves tokens for the model's response generation |

## Error Responses

### 400 Bad Request

```json
{
  "error": "Bad Request",
  "message": "Invalid parameter values",
  "details": {
    "fieldErrors": [
      {
        "field": "globalParameters.temperature",
        "message": "Temperature must be between 0.0 and 1.0"
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
  "message": "Admin role required to modify DeepSeek parameters",
  "details": null
}
```

### 404 Not Found

```json
{
  "error": "Not Found",
  "message": "NPC with ID invalid_npc_id not found",
  "details": null
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred while updating DeepSeek parameters",
  "details": null
}
```

## Implementation Notes

- This endpoint provides fine-grained control over the DeepSeek 7B language model used for NPC interactions
- Parameter adjustments can dramatically impact NPC conversation quality and character consistency
- Global parameters serve as defaults for all NPCs
- NPC-specific overrides take precedence over global parameters
- The `applyImmediately` flag determines if changes affect ongoing conversations:
  - `true`: Changes apply to all new dialogue turns, including ongoing conversations
  - `false`: Changes only apply to new conversations started after the update
- Parameter changes are logged for audit and monitoring purposes
- This endpoint is meant for administrative optimization rather than regular gameplay
- Extreme parameter values may result in poor dialogue quality or unexpected NPC behavior
- Using this endpoint requires understanding of language model concepts and their effects on dialogue
- Parameters are automatically validated to ensure they fall within acceptable ranges
- The system may reject parameter combinations that would result in poor performance
- While all parameters are optional, providing `null` explicitly resets that parameter to the system default
- For detailed information on DeepSeek parameters, refer to the [NPC AI Architecture](../docs/ai/Tokyo%20Train%20Station%20Adventure%3A%20NPC%20AI%20Architecture.md) documentation
