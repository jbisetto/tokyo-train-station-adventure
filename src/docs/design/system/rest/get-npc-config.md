# Get NPC Configuration Endpoint

Endpoint for retrieving the configuration for a specific NPC in the Tokyo Train Station Adventure game.

**URL:** `/api/npc/config/{npcId}`

**Method:** `GET`

**Authentication Required:** Yes (via session token)

**Role Required:** Admin (standard players cannot access NPC configurations)

## Request

```http
GET /api/npc/config/{npcId}
```

### URL Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `npcId` | string | Unique identifier for the NPC | Yes |

## Response

```json
{
  "npcId": "string",
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

| Field | Type | Description |
|-------|------|-------------|
| `npcId` | string | Unique identifier for the NPC |
| `profile` | object | General profile information about the NPC |
| `profile.name` | string | The NPC's display name |
| `profile.role` | string | The NPC's role in the train station |
| `profile.location` | string | The NPC's primary location |
| `profile.personality` | array | List of personality traits |
| `profile.expertise` | array | Topics the NPC is knowledgeable about |
| `profile.limitations` | array | Topics the NPC is not knowledgeable about |
| `languageProfile` | object | Language-related characteristics |
| `languageProfile.defaultLanguage` | string | Primary language of the NPC |
| `languageProfile.japaneseLevel` | string | JLPT level of Japanese used by the NPC |
| `languageProfile.speechPatterns` | array | Characteristic speech patterns |
| `languageProfile.commonPhrases` | array | Frequently used phrases |
| `languageProfile.vocabularyFocus` | array | Vocabulary domains this NPC emphasizes |
| `promptTemplates` | object | Templates used for AI prompt construction |
| `promptTemplates.initialGreeting` | string | Template for initial greeting |
| `promptTemplates.responseFormat` | string | Format specification for responses |
| `promptTemplates.errorHandling` | string | Template for handling errors |
| `promptTemplates.conversationClose` | string | Template for ending conversations |
| `conversationParameters` | object | Parameters controlling conversation behavior |
| `conversationParameters.maxTurns` | integer | Maximum number of conversation turns |
| `conversationParameters.temperatureDefault` | number | Default temperature for AI generation |
| `conversationParameters.contextWindowSize` | integer | Size of context window for conversation history |

## Example Response

```json
{
  "npcId": "ticket_operator",
  "profile": {
    "name": "Tanaka",
    "role": "Ticket Machine Operator",
    "location": "Ticket Gate Area",
    "personality": [
      "Helpful",
      "Technical",
      "Patient",
      "Efficient",
      "Detail-oriented"
    ],
    "expertise": [
      "Ticket types",
      "Fares",
      "Machine operation",
      "Payment methods",
      "Route information"
    ],
    "limitations": [
      "Only knows about Tokyo Station",
      "Limited knowledge of special events",
      "Cannot assist with non-transportation issues"
    ]
  },
  "languageProfile": {
    "defaultLanguage": "japanese",
    "japaneseLevel": "N5",
    "speechPatterns": [
      "Polite but direct instruction giving",
      "Uses technical ticket terminology",
      "Clear step-by-step guidance",
      "Uses official station announcements style"
    ],
    "commonPhrases": [
      "このボタンを押してください",
      "～円です",
      "片道ですか、往復ですか？",
      "切符はここから出てきます",
      "お手伝いできますか？"
    ],
    "vocabularyFocus": [
      "transportation",
      "directions",
      "money",
      "time"
    ]
  },
  "promptTemplates": {
    "initialGreeting": "いらっしゃいませ。切符の購入をお手伝いします。どちらまで行かれますか？ (Welcome. I can help you purchase a ticket. Where would you like to go?)",
    "responseFormat": "{japanese_text} ({english_translation})",
    "errorHandling": "すみません、もう一度言っていただけますか？ (I'm sorry, could you please say that again?)",
    "conversationClose": "良い旅を！ (Have a good trip!)"
  },
  "conversationParameters": {
    "maxTurns": 15,
    "temperatureDefault": 0.7,
    "contextWindowSize": 2048
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

### 403 Forbidden

```json
{
  "error": "Forbidden",
  "message": "Admin role required to access NPC configurations",
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
  "message": "An unexpected error occurred while retrieving NPC configuration",
  "details": null
}
```

## Implementation Notes

- This endpoint is primarily for administrative use to view and manage NPC configurations
- The configurations control how NPCs behave in dialogue interactions
- These configurations are used by the NPC AI system described in the [NPC AI Architecture](../docs/ai/Tokyo%20Train%20Station%20Adventure%3A%20NPC%20AI%20Architecture.md) document
- The prompt templates are used to construct prompts for the DeepSeek 7B model and other AI tiers
- The language profile ensures that NPCs use appropriate Japanese for JLPT N5 learners
- Personality traits and expertise domains influence the NPC's dialogue style and knowledge
- Changes to NPC configurations take effect immediately for new conversations
- When using this endpoint programmatically, consider caching responses as configurations change infrequently
- Related endpoint: [Update NPC Configuration](update-npc-config.md) for modifying these settings
