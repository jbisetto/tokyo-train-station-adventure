# Player Progress Endpoint

Endpoint for retrieving the player's Japanese language learning progress in the Tokyo Train Station Adventure game.

**URL:** `/api/player/progress/{playerId}`

**Method:** `GET`

**Authentication Required:** Yes (via session token)

## Request

```http
GET /api/player/progress/{playerId}
```

### URL Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `playerId` | string | Unique identifier for the player | Yes |

## Response

```json
{
  "player": {
    "id": "string",
    "level": "N5"
  },
  "progress": {
    "vocabulary": {
      "total": "number",
      "mastered": "number",
      "learning": "number",
      "needsReview": "number",
      "percentComplete": "number"
    },
    "grammar": {
      "total": "number",
      "mastered": "number",
      "learning": "number",
      "needsReview": "number",
      "percentComplete": "number",
      "accuracyRates": {
        "particles": "number",
        "verbForms": "number",
        "sentences": "number"
      }
    },
    "conversation": {
      "successRate": "number",
      "completedExchanges": "number"
    }
  },
  "achievements": ["string"],
  "recommendations": {
    "focusAreas": ["string"],
    "suggestedActivities": ["string"]
  },
  "vocabulary": {
    "mastered": [
      {
        "word": "string",
        "reading": "string",
        "meaning": "string",
        "examples": ["string"]
      }
    ],
    "learning": [
      {
        "word": "string",
        "reading": "string",
        "meaning": "string",
        "masteryLevel": "number",
        "lastSeen": "string"
      }
    ],
    "forReview": [
      {
        "word": "string",
        "reading": "string",
        "meaning": "string",
        "dueForReview": "boolean"
      }
    ]
  },
  "grammarPoints": {
    "mastered": [
      {
        "pattern": "string",
        "explanation": "string",
        "examples": ["string"]
      }
    ],
    "learning": [
      {
        "pattern": "string",
        "explanation": "string",
        "masteryLevel": "number"
      }
    ],
    "forReview": [
      {
        "pattern": "string",
        "explanation": "string",
        "dueForReview": "boolean"
      }
    ]
  },
  "visualizationData": {
    "skillPentagon": {
      "reading": "number",
      "writing": "number",
      "listening": "number",
      "speaking": "number",
      "vocabulary": "number"
    },
    "progressOverTime": [
      {
        "date": "string",
        "vocabularyMastered": "number",
        "grammarMastered": "number"
      }
    ]
  }
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `player` | object | Basic player information |
| `player.id` | string | Unique player identifier |
| `player.level` | string | Current JLPT level (N5, N4, etc.) |
| `progress` | object | Overall progress metrics |
| `progress.vocabulary` | object | Vocabulary acquisition statistics |
| `progress.grammar` | object | Grammar mastery statistics |
| `progress.conversation` | object | Conversation success metrics |
| `achievements` | array | List of language-related achievements |
| `recommendations` | object | Personalized learning recommendations |
| `recommendations.focusAreas` | array | Areas needing additional practice |
| `recommendations.suggestedActivities` | array | Suggested learning activities |
| `vocabulary` | object | Detailed vocabulary knowledge |
| `vocabulary.mastered` | array | Fully learned vocabulary items |
| `vocabulary.learning` | array | Vocabulary in progress |
| `vocabulary.forReview` | array | Vocabulary needing review |
| `grammarPoints` | object | Detailed grammar knowledge |
| `grammarPoints.mastered` | array | Fully learned grammar patterns |
| `grammarPoints.learning` | array | Grammar patterns in progress |
| `grammarPoints.forReview` | array | Grammar patterns needing review |
| `visualizationData` | object | Data for progress visualizations |
| `visualizationData.skillPentagon` | object | Five language skill metrics |
| `visualizationData.progressOverTime` | array | Historical progress data |

### Mastery Level Values

The `masteryLevel` field represents the player's mastery of vocabulary or grammar on a scale from 0.0 to 1.0:

| Range | Interpretation |
|-------|----------------|
| 0.0 - 0.3 | Needs review, minimal recognition |
| 0.3 - 0.6 | Learning, partial understanding |
| 0.6 - 0.8 | Good understanding, occasional errors |
| 0.8 - 1.0 | Mastered, consistent correct usage |

## Example Response

```json
{
  "player": {
    "id": "player123",
    "level": "N5"
  },
  "progress": {
    "vocabulary": {
      "total": 86,
      "mastered": 42,
      "learning": 31,
      "needsReview": 13,
      "percentComplete": 48.8
    },
    "grammar": {
      "total": 24,
      "mastered": 11,
      "learning": 8,
      "needsReview": 5,
      "percentComplete": 45.8,
      "accuracyRates": {
        "particles": 0.78,
        "verbForms": 0.65,
        "sentences": 0.71
      }
    },
    "conversation": {
      "successRate": 0.82,
      "completedExchanges": 27
    }
  },
  "achievements": [
    "first_conversation_completed",
    "ticket_purchased",
    "five_new_vocabulary_mastered",
    "particle_master_level_1"
  ],
  "recommendations": {
    "focusAreas": [
      "verb_conjugation",
      "station_vocabulary",
      "direction_phrases"
    ],
    "suggestedActivities": [
      "practice_ticket_machine_dialogue",
      "review_direction_vocabulary",
      "complete_station_announcement_challenge"
    ]
  },
  "vocabulary": {
    "mastered": [
      {
        "word": "切符",
        "reading": "きっぷ",
        "meaning": "ticket",
        "examples": [
          "切符を買います。",
          "切符はどこで買えますか？"
        ]
      },
      {
        "word": "電車",
        "reading": "でんしゃ",
        "meaning": "train",
        "examples": [
          "電車に乗ります。",
          "電車は何時に来ますか？"
        ]
      }
    ],
    "learning": [
      {
        "word": "改札",
        "reading": "かいさつ",
        "meaning": "ticket gate",
        "masteryLevel": 0.56,
        "lastSeen": "2025-03-08T14:22:30Z"
      },
      {
        "word": "遅延",
        "reading": "ちえん",
        "meaning": "delay",
        "masteryLevel": 0.42,
        "lastSeen": "2025-03-09T10:15:45Z"
      }
    ],
    "forReview": [
      {
        "word": "乗り換え",
        "reading": "のりかえ",
        "meaning": "transfer (trains)",
        "dueForReview": true
      },
      {
        "word": "特急",
        "reading": "とっきゅう",
        "meaning": "express train",
        "dueForReview": false
      }
    ]
  },
  "grammarPoints": {
    "mastered": [
      {
        "pattern": "〜ます",
        "explanation": "Polite present affirmative verb ending",
        "examples": [
          "行きます (I go/will go)",
          "買います (I buy/will buy)"
        ]
      },
      {
        "pattern": "〜ください",
        "explanation": "Please do ~",
        "examples": [
          "見てください (Please look)",
          "教えてください (Please tell me)"
        ]
      }
    ],
    "learning": [
      {
        "pattern": "〜てもいいですか",
        "explanation": "May I ~?/Is it okay if I ~?",
        "masteryLevel": 0.65
      },
      {
        "pattern": "〜なければなりません",
        "explanation": "Must do ~/Have to do ~",
        "masteryLevel": 0.45
      }
    ],
    "forReview": [
      {
        "pattern": "〜たことがあります",
        "explanation": "Have experience doing ~",
        "dueForReview": true
      },
      {
        "pattern": "〜ながら",
        "explanation": "While doing ~",
        "dueForReview": false
      }
    ]
  },
  "visualizationData": {
    "skillPentagon": {
      "reading": 0.62,
      "writing": 0.48,
      "listening": 0.71,
      "speaking": 0.54,
      "vocabulary": 0.65
    },
    "progressOverTime": [
      {
        "date": "2025-03-01",
        "vocabularyMastered": 25,
        "grammarMastered": 8
      },
      {
        "date": "2025-03-05",
        "vocabularyMastered": 34,
        "grammarMastered": 9
      },
      {
        "date": "2025-03-10",
        "vocabularyMastered": 42,
        "grammarMastered": 11
      }
    ]
  }
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

### 404 Not Found

```json
{
  "error": "Not Found",
  "message": "Player with ID player123 not found",
  "details": null
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred while retrieving player progress",
  "details": null
}
```

## Implementation Notes

- This endpoint retrieves data from the Learning Progress Tracker component described in the [Python Game Logic Architecture](../docs/design/Tokyo%20Train%20Station%20Adventure%20-%20Python%20Game%20Logic%20Architecture.md)
- Progress tracking follows the methodology outlined in the [Key Development Considerations](../docs/ai/Tokyo%20Train%20Station%20Adventure%3A%20Key%20Development%20Considerations.md) document
- The response is transformed through the adapter layer as detailed in the [API Design Document](adapter-design.md)
- This endpoint supports the Learning Progress UI components described in the [User Interface Components](../docs/ui/Tokyo%20Train%20Station%20Adventure%3A%20User%20Interface%20Components.md) document
