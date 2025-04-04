# Tokyo Train Station Adventure
## API Testing Strategy

This document outlines the testing strategy for the RESTful API that connects the frontend (Phaser.js) and backend (Python) components of the Tokyo Train Station Adventure language learning game.

## Testing Approach

Our API testing strategy follows a domain-driven, bottom-up approach that aligns with the overall architecture of the project. The strategy prioritizes testing components with fewer dependencies first, then gradually expanding to more complex integration scenarios.

## Test Organization

The tests are organized around the key domains in the project:

| Domain | Description | Testing Focus |
|--------|-------------|--------------|
| Companion AI | Dog companion's assistance functionality | Response formatting, AI tier selection, language help |
| Dialogue Processing | NPC and player interactions | Language validation, correctness feedback, conversation flow |
| Player Progress | Learning progress tracking | Progress calculations, learning recommendations, data persistence |
| Game State | Game saving and loading | State serialization, persistence, retrieval |

## Testing Layers

### 1. Unit Tests

Focus on testing individual components in isolation:

- **Adapter Tests**: Verify transformation between internal and external formats
- **Validation Tests**: Ensure request validation works correctly
- **Rule-Based Processing Tests**: Validate rule-based response generation

### 2. Integration Tests

Test the interaction between components:

- **API Endpoint Tests**: Verify endpoints handle requests and return proper responses
- **AI Router Tests**: Confirm correct tier selection (rule → local → cloud)
- **Database Integration Tests**: Test persistence of game state and player progress

### 3. Contract Tests

Ensure the API fulfills its contract with the frontend:

- **Schema Validation**: Verify all responses match their JSON schema definitions
- **Field Requirements**: Confirm required fields are always present
- **Type Consistency**: Ensure field types remain consistent

### 4. End-to-End API Tests

Test complete user scenarios:

- **Companion Assistance Flows**: Test full assist request/response cycles
- **Dialogue Scenarios**: Test complete conversation exchanges
- **Learning Progress Scenarios**: Test tracking and reporting of learning milestones

## Testing the Tiered AI Approach

Special consideration is given to testing the three-tier AI implementation:

| Tier | Coverage | Testing Approach |
|------|----------|------------------|
| Tier 1: Rule-Based (70%) | 100% | Deterministic test cases with known inputs/outputs |
| Tier 2: Local Model (20%) | 90% | Structural validation plus key scenario testing |
| Tier 3: Cloud Services (10%) | 80% | Focus on integration, fallbacks, and error handling |

### AI Tier Testing Strategy

1. **Routing Tests**: Verify requests are routed to the appropriate tier
2. **Tier Isolation Tests**: Test each tier's processing independently
3. **Fallback Tests**: Verify graceful degradation when a tier fails
4. **Performance Tests**: Measure and compare response times across tiers

## Test Directory Structure

```
tokyo-train-station-adventure/
├── tests/
│   ├── api/
│   │   ├── unit/
│   │   │   ├── test_adapters.py
│   │   │   └── test_request_validation.py
│   │   ├── integration/
│   │   │   ├── test_companion_api.py
│   │   │   ├── test_dialogue_api.py
│   │   │   ├── test_progress_api.py
│   │   │   └── test_game_state_api.py
│   │   ├── contract/
│   │   │   ├── schemas/
│   │   │   └── test_api_contracts.py
│   │   └── e2e/
│   │       ├── test_companion_flows.py
│   │       └── test_dialogue_flows.py
│   └── ai/
│       ├── test_tier_routing.py
│       ├── test_rule_based.py
│       └── test_local_model.py
```

## Testing Tools

| Tool | Purpose |
|------|---------|
| pytest | Test runner and framework |
| pytest-mock | Mocking dependencies |
| requests | Making HTTP requests in tests |
| jsonschema | JSON schema validation |
| FastAPI TestClient | Testing endpoints without HTTP |

## Example Test Implementation

### Unit Test for Response Adapter

```python
# tests/api/unit/test_adapters.py
import pytest
from backend.api.adapters.companion_response_adapter import CompanionResponseAdapter

def test_companion_response_adaptation():
    # Given an internal response format
    internal_response = {
        "responseId": "test-123",
        "responseText": "Woof! That's the ticket machine.",
        "japanesePhrase": "切符売機",
        "pronunciation": "kippu-uriki",
        "companionAction": "POINT_AT_SCREEN",
        "companionEmotion": "excited",
        "highlightElements": ["ticket_machine"],
        "suggestions": ["How do I buy a ticket?"],
        "learningMoments": ["ticket_machine_vocabulary"],
    }
    
    # When adapting to external format
    result = CompanionResponseAdapter.adapt(internal_response)
    
    # Then verify the transformation
    assert result["dialogue"]["text"] == "Woof! That's the ticket machine."
    assert result["dialogue"]["japanese"] == "切符売機"
    assert result["companion"]["animation"] == "pointing"  # Mapped from POINT_AT_SCREEN
    assert result["companion"]["emotionalState"] == "excited"
    assert len(result["ui"]["highlights"]) == 1
    assert result["ui"]["highlights"][0]["id"] == "ticket_machine"
    assert result["gameState"]["learningMoments"] == ["ticket_machine_vocabulary"]
    assert result["meta"]["responseId"] == "test-123"
```

### Integration Test for AI Tier Routing

```python
# tests/ai/test_tier_routing.py
import pytest
from backend.ai.router import AIRouter

def test_tier_routing_rule_based():
    # Given a simple request that should be handled by rules
    router = AIRouter()
    request = {
        "inputText": "小田原までの切符をください",  # Ticket to Odawara please
        "inputType": "keyboard",
        "contextId": "ticket_machine_interaction",
    }
    
    # When determining which tier should handle it
    tier = router.determine_processing_tier(request)
    
    # Then verify it routes to Tier 1 (rule-based)
    assert tier == "rule"
```

## Testing Goals

| Goal | Target | Measurement |
|------|--------|-------------|
| API Coverage | 90%+ | Test coverage reporting |
| Contract Compliance | 100% | Schema validation passing |
| Error Handling | 100% | All error cases tested |
| Performance | <200ms (T1), <500ms (T2), <2s (T3) | Response time metrics |
| Security | 100% | Auth/permission tests passing |

## Implementation Roadmap

1. **Setup Testing Framework**: Configure pytest and supporting tools
2. **Implement Adapter Tests**: Test transformation logic first
3. **Add Integration Tests**: Test API endpoints with mocked services
4. **Create Contract Tests**: Define and validate API schema contracts
5. **Develop E2E API Tests**: Test complete flows through the API
6. **Implement AI Tier Tests**: Test tier routing and processing
7. **Add Performance Tests**: Measure and optimize response times
8. **Continuous Integration**: Automate test runs in CI pipeline

This testing strategy ensures the API reliably supports the Tokyo Train Station Adventure game while maintaining the balance between cost-effective implementation and robust functionality.
