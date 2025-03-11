# Scenario Detection Implementation

## Overview

The scenario detection system is a key component of the Tier 3 processing in the Tokyo Train Station Adventure's companion AI. It enables the AI to identify specific types of player requests and route them to specialized handlers that can provide more tailored and contextually appropriate responses.

## Architecture

The scenario detection system consists of the following components:

1. **ScenarioType Enum**: Defines the different types of scenarios that can be detected:
   - Ticket Purchase
   - Navigation
   - Vocabulary Help
   - Grammar Explanation
   - Cultural Information
   - Unknown (fallback)

2. **ScenarioDetector Class**: The main class responsible for:
   - Detecting the scenario type based on the classified request
   - Routing the request to the appropriate specialized handler
   - Providing fallback mechanisms when no specific scenario is detected

3. **Specialized Handlers**: A set of handler classes, each designed to handle a specific scenario type:
   - `TicketPurchaseHandler`: Handles requests related to buying tickets
   - `NavigationHandler`: Handles requests for directions and finding locations
   - `VocabularyHelpHandler`: Handles requests for vocabulary explanations
   - `GrammarExplanationHandler`: Handles requests for grammar explanations
   - `CulturalInformationHandler`: Handles requests for cultural information

## Detection Logic

The scenario detection uses a rule-based approach with the following methods:

1. **Ticket Purchase Detection**:
   - Checks for ticket-related keywords (ticket, buy, purchase, fare, kippu)
   - Verifies the presence of a destination entity
   - Confirms the intent is related to general hints or transactions

2. **Navigation Detection**:
   - Checks for navigation-related keywords (where, how to get, find, platform, etc.)
   - Verifies the presence of a location entity
   - Confirms the intent is related to direction guidance

3. **Vocabulary Help Detection**:
   - Checks if the intent is vocabulary help
   - Verifies the presence of a word entity
   - Looks for vocabulary-related keywords (mean, translate, what is, etc.)

4. **Grammar Explanation Detection**:
   - Checks if the intent is grammar explanation
   - Verifies the presence of a grammar point entity
   - Looks for grammar-related keywords (grammar, structure, conjugate, etc.)

5. **Cultural Information Detection**:
   - Checks for cultural-related keywords (culture, custom, tradition, etc.)
   - Verifies the presence of a topic entity

## Integration with Other Components

The scenario detection system integrates with:

1. **Tier3Processor**: The processor uses the scenario detector to handle complex requests.
2. **RequestHandler**: The main request handler routes complex requests to the Tier3Processor, which then uses the scenario detector.
3. **ContextManager**: The scenario detector uses the context manager to retrieve conversation context for more informed handling.
4. **BedrockClient**: The specialized handlers use the Bedrock client to generate appropriate responses.

## Testing Strategy

The scenario detection system is thoroughly tested with:

1. **Unit Tests**: Testing individual components like the scenario detector and specialized handlers.
2. **Integration Tests**: Testing the interaction between the scenario detector and other components like the Tier3Processor and RequestHandler.
3. **Scenario-specific Tests**: Testing the detection and handling of each specific scenario type.

## Future Enhancements

Potential future enhancements for the scenario detection system:

1. **Machine Learning-based Detection**: Replace or augment the rule-based approach with a machine learning model for more accurate scenario detection.
2. **Additional Scenario Types**: Add support for more specialized scenarios as the game evolves.
3. **Personalized Scenario Handling**: Adapt the scenario handling based on the player's language level and past interactions.
4. **Multi-scenario Detection**: Handle requests that might span multiple scenarios.

## Conclusion

The scenario detection system enhances the companion AI's ability to provide contextually appropriate and helpful responses to complex player requests. By routing requests to specialized handlers, it ensures that players receive the most relevant assistance for their specific needs, whether they're trying to buy a ticket, navigate the station, learn vocabulary, understand grammar, or learn about Japanese culture. 