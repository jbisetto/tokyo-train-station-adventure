# Scenario Detection Implementation

## Overview

The Scenario Detection module is a key component of the Tier 3 processing system in the Tokyo Train Station Adventure companion AI. It enables the AI to identify specific types of player requests and route them to specialized handlers that are optimized for those scenarios.

This document outlines the design, implementation, and usage of the scenario detection system.

## Architecture

The scenario detection system consists of the following components:

1. **ScenarioDetector**: The main class responsible for detecting scenarios and routing requests to appropriate handlers.
2. **ScenarioType**: An enum defining the different types of scenarios that can be detected.
3. **Specialized Handlers**: A set of handler classes, each designed to handle a specific type of scenario.
4. **Integration with Tier3Processor**: Logic to incorporate scenario detection into the processing pipeline.

### Workflow

1. A player request is received and classified by the intent classifier.
2. The Tier3Processor receives the classified request.
3. The ScenarioDetector analyzes the request to determine if it matches a known scenario.
4. If a match is found, the request is routed to the appropriate specialized handler.
5. The handler processes the request and generates a response tailored to the scenario.
6. If no match is found, the request is processed using the standard conversation flow.

## Scenario Types

The system currently supports the following scenario types:

- **Ticket Purchase**: Helping players buy train tickets, understand fares, etc.
- **Navigation**: Assisting players in finding their way around the station.
- **Vocabulary Help**: Explaining Japanese words and phrases.
- **Grammar Explanation**: Providing explanations of Japanese grammar points.
- **Cultural Information**: Sharing information about Japanese culture and customs.

## Detection Logic

The ScenarioDetector uses a combination of factors to identify scenarios:

1. **Intent Classification**: The primary intent category assigned to the request.
2. **Entity Extraction**: Specific entities mentioned in the request (e.g., destinations, words, grammar points).
3. **Keyword Matching**: Presence of scenario-specific keywords in the player's input.

Each scenario type has its own detection rule method that evaluates these factors to determine if the request matches that scenario.

## Specialized Handlers

Each scenario type has a corresponding specialized handler that:

1. Creates optimized prompts tailored to the specific scenario.
2. Incorporates relevant context from the conversation history.
3. Formats responses in a way that's most helpful for that scenario type.
4. Provides additional information specific to the scenario (e.g., Japanese phrases for ticket purchasing).

## Implementation Details

### ScenarioDetector Class

The ScenarioDetector class maintains:

- A registry of handlers for each scenario type
- Detection rules for each scenario type
- Methods for detecting scenarios and routing requests

### Integration with Tier3Processor

The Tier3Processor has been updated to:

1. Initialize a ScenarioDetector instance
2. Attempt scenario detection for complex requests
3. Route requests to specialized handlers when a scenario is detected
4. Fall back to the standard processing flow when no scenario is detected

## Testing

The scenario detection system is thoroughly tested with unit tests that verify:

1. Scenario detection for various request types
2. Handler selection based on detected scenarios
3. Response generation for different scenarios
4. Integration with the Tier3Processor

## Future Enhancements

Potential future enhancements to the scenario detection system include:

1. **Additional Scenario Types**: Adding support for more specialized scenarios.
2. **Machine Learning-Based Detection**: Using ML to improve scenario detection accuracy.
3. **Personalization**: Tailoring scenario handling based on player preferences and history.
4. **Multi-Scenario Detection**: Handling requests that span multiple scenarios.
5. **Feedback Loop**: Incorporating player feedback to improve scenario detection and handling.

## Usage Example

```python
# Example of using the scenario detection system
from backend.ai.companion.tier3.scenario_detection import ScenarioDetector
from backend.ai.companion.tier3.context_manager import ContextManager
from backend.ai.companion.tier3.bedrock_client import BedrockClient

# Initialize components
detector = ScenarioDetector()
context_manager = ContextManager()
bedrock_client = BedrockClient()

# Process a request
scenario_type = detector.detect_scenario(classified_request)
if scenario_type != ScenarioType.UNKNOWN:
    response = detector.handle_scenario(
        classified_request,
        context_manager,
        bedrock_client
    )
```

## Conclusion

The scenario detection system enhances the companion AI's ability to provide tailored, helpful responses to specific types of player requests. By routing requests to specialized handlers, the system can deliver more accurate, contextually appropriate, and helpful responses, improving the overall player experience. 