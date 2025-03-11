feat(tier3): implement scenario detection system

Implements a scenario detection system for the Tier 3 processor that identifies specific types of player requests and routes them to specialized handlers. This enhances the companion AI's ability to provide tailored, contextually appropriate responses.

Key components:
- Created ScenarioDetector class to analyze requests and identify scenarios
- Defined ScenarioType enum for categorizing different scenario types
- Implemented detection rules for ticket purchase, navigation, vocabulary help, grammar explanation, and cultural information scenarios
- Integrated scenario detection with the Tier3Processor
- Added comprehensive tests for all scenario detection functionality
- Created documentation explaining the scenario detection system

This completes task 4.2.4 in the implementation plan and finalizes the "Build Complex Scenario Handlers" milestone.

Tests: All tests passing (74 tests)
Documentation: Added docs/design/scenario-detection.md 