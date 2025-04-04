# Update NPC Configuration Endpoint

Endpoint for updating the configuration for a specific NPC in the Tokyo Train Station Adventure game.

**URL:** `/api/npc/config/{npcId}`

**Method:** `PUT`

**Authentication Required:** Yes (via session token)

**Role Required:** Admin (standard players cannot modify NPC configurations)

## Request

```http
PUT /api/npc/config/{npcId}
Content-Type: application/json
```

### URL Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `npcId` | string | Unique identifier for the NPC | Yes |

### Request Body

```json
{
  "profile": {
    "name": "string",
    "role": "string",
    "location": "string",
    "personality": ["string"],
    "expertise": ["string"],
    "limitations": ["string"]
  },
  "languageProfile": {
    "defaultLanguage": "string",
    "japaneseLevel": "string",
    "speechPatterns": ["string"],
    "commonPhrases": ["string"],
    "vocabularyFocus": ["string"]
  },
  "promptTemplates": {
    "initialGreeting": "string",
    "responseFormat": "string",
    "errorHandling": "string",
    "conversationClose": "string"
  },
  "conversationParameters": {
    "maxTurns": "integer",
    "temperatureDefault": "number",
    "contextWindowSize": "integer"
  }
}
```

### Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `profile` | object | General profile information about the NPC | No |
| `profile.name` | string | The NPC's display name | No |
| `profile.role` | string | The NPC's role in the train station | No |
| `profile.location` | string | The NPC's primary location | No |
| `profile.personality` | array | List of personality traits | No |
| `profile.expertise` | array | Topics the NPC is knowledgeable about | No |
| `profile.limitations` | array | Topics the NPC is not knowledgeable about | No |
| `languageProfile` | object | Language-related characteristics | No |
| `languageProfile.defaultLanguage` | string | Primary language of the NPC | No |
| `languageProfile.japaneseLevel` | string | JLPT level of Japanese used by the NPC | No |
| `languageProfile.speechPatterns` | array | Characteristic speech patterns | No |
| `languageProfile.commonPhrases` | array | Frequently used phrases | No |
| `languageProfile.vocabularyFocus` | array | Vocabulary domains this NPC emphasizes | No |
| `promptTemplates` | object | Templates used for AI prompt construction | No |
| `promptTemplates.initialGreeting` | string | Template for initial greeting | No |
| `promptTemplates.responseFormat` | string | Format specification for responses | No |
| `promptTemplates.errorHandling` | string | Template for handling errors | No |
| `promptTemplates.conversationClose` | string | Template for ending conversations | No |
| `conversationParameters` | object | Parameters controlling conversation behavior | No |
| `conversationParameters.maxTurns` | integer | Maximum number of conversation turns | No |
| `conversationParameters.temperatureDefault` | number | Default temperature for AI generation | No |
| `conversationParameters.contextWindowSize` | integer | Size of context window for conversation history | No |

Note: All fields are optional in the request. Only the fields that need to be updated should be included. Omitted fields will remain unchanged.

## Response

```json
{
  "success": "boolean",
  "message": "string",
  "npcId": "string",
  "modifiedAt": "string"
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the update operation was successful |
| `message` | string | A message describing the result of the operation |
| `npcId` | string | The identifier of the updated NPC |
| `modifiedAt` | string | ISO 8601 formatted timestamp of when the update was processed |

## Example Request

```json
{
  "profile": {
    "name": "Tanaka",
    "personality": [
      "Helpful",
      "Technical",
      "Patient",
      "Enthusiastic",
      "Detail-oriented"
    ]
  },
  "languageProfile": {
    "commonPhrases": [
      "このボタンを押してください",
      "～円です",
      "片道ですか、往復ですか？",
      "切符はここから出てきます",
      "お手伝いできますか？",
      "いい旅を！"
    ]
  },
  "conversationParameters": {
    "temperatureDefault": 0.65
  }
}
```

## Example Response

```json
{
  "success": true,
  "message": "NPC configuration updated successfully",
  "npcId": "ticket_operator",
  "modifiedAt": "2025-03-12T09:45:22Z"
}
```

## Error Responses

### 400 Bad Request

```json
{
  "error": "Bad Request",
  "message": "Invalid request format or invalid field values",
  "details": {
    "fieldErrors": [
      {
        "field": "conversationParameters.temperatureDefault",
        "message": "Value must be between 0.0 and 1.0"
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
  "message": "Admin role required to modify NPC configurations",
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

### 409 Conflict

```json
{
  "error": "Conflict",
  "message": "NPC configuration was modified by another request",
  "details": {
    "lastModified": "2025-03-12T09:44:55Z"
  }
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred while updating NPC configuration",
  "details": null
}
```

## Implementation Notes

- This endpoint allows partial updates - only the fields included in the request will be modified
- Validation is performed on all updated fields to ensure consistency and correctness
- Updated configurations are immediately applied to new NPC interactions
- Active conversations with the NPC will continue to use the previous configuration until completion
- All configuration changes are logged for audit purposes
- The configuration update is performed atomically - either all fields are updated or none
- Field constraints:
  - `temperatureDefault` must be between 0.0 and 1.0
  - `maxTurns` must be between 1 and 100
  - `contextWindowSize` must not exceed 8192 tokens
  - `japaneseLevel` must be one of: N5, N4, N3, N2, N1
- When updating array fields (like `personality` or `commonPhrases`), the provided array replaces the existing array completely
- Related endpoint: [Get NPC Configuration](get-npc-config.md) for retrieving current configurations
