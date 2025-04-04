# Personality Engine

The Personality Engine is a core component of the Tokyo Train Station Adventure's companion AI system. It manages the companion's personality traits, adapts to player preferences, and enhances responses with personality-based modifications.

## Overview

The Personality Engine provides a flexible and adaptive personality system for the companion AI, allowing it to:

- Maintain multiple personality profiles with different traits
- Adapt to player preferences and interaction patterns
- Analyze player requests for personality cues
- Enhance responses with appropriate emotional expressions and suggestions
- Track player feedback to improve future interactions

## Key Components

### Personality Configuration

The personality configuration system manages personality traits and profiles:

- **PersonalityTrait**: Represents a single personality trait with a value and valid range
- **PersonalityProfile**: Encapsulates a complete personality profile with multiple traits and settings
- **PersonalityConfig**: Manages multiple personality profiles and provides access to the active profile

### Personality Engine

The PersonalityEngine class is responsible for:

- Loading and managing personality profiles
- Adapting the companion's personality based on player interactions
- Analyzing player requests for personality cues
- Enhancing responses with personality-based modifications
- Processing player feedback to adjust preferences

## Personality Traits

The system includes several key personality traits:

- **Friendliness** (0.0 = cold, 1.0 = very friendly)
- **Enthusiasm** (0.0 = subdued, 1.0 = very enthusiastic)
- **Helpfulness** (0.0 = minimal help, 1.0 = very helpful)
- **Playfulness** (0.0 = serious, 1.0 = very playful)
- **Formality** (0.0 = casual, 1.0 = very formal)
- **Patience** (0.0 = impatient, 1.0 = very patient)
- **Curiosity** (0.0 = incurious, 1.0 = very curious)

## Adaptation Mechanisms

The Personality Engine adapts to player preferences through several mechanisms:

1. **Player Feedback Analysis**: Analyzes explicit feedback from the player to adjust preferences
2. **Request Analysis**: Detects personality cues in player requests (formality, detail preference, etc.)
3. **Interaction Tracking**: Monitors positive and negative interactions to adjust traits like enthusiasm
4. **Periodic Adaptation**: Gradually adapts personality traits based on accumulated preferences

## Response Enhancement

The Personality Engine enhances responses by:

- Selecting appropriate emotional expressions based on formality and context
- Adding learning cues for players who prefer detailed information
- Generating suggested actions based on the topic and helpfulness trait
- Adjusting the tone and style of responses based on personality traits

## Integration with Response Formatter

The Personality Engine integrates with the Response Formatter to apply personality traits to responses:

1. The Response Formatter receives personality traits from the Personality Engine
2. Traits influence the selection of openings, closings, and emotional expressions
3. The formatted response reflects the companion's personality profile

## Usage Example

```python
# Initialize the personality engine
engine = PersonalityEngine()

# Analyze a player request
analysis = engine.analyze_request(player_request)

# Enhance a response with personality
enhanced_response = engine.enhance_response(raw_response, analysis)

# Process player feedback
engine.process_player_feedback(request_id, feedback_text, rating)

# Adapt personality based on interactions (called periodically)
engine.adapt_to_player()
```

## Configuration

The default personality profile ("Hachiko") is designed to be friendly, helpful, and patient, with a focus on assisting with Japanese language learning. Additional profiles can be created and customized through the API.

## Future Enhancements

Planned enhancements to the Personality Engine include:

- More sophisticated emotion state tracking
- Learning style detection and adaptation
- Cultural sensitivity adjustments
- Mood-based response variations
- Memory of player preferences for specific topics 