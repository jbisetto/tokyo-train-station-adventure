"""
Example script to show the OpenAI conversation format in prompts.
"""

from backend.ai.companion.core.conversation_manager import ConversationManager, ConversationState
from backend.ai.companion.core.models import (
    ClassifiedRequest,
    IntentCategory,
    ComplexityLevel,
    ProcessingTier
)
from datetime import datetime

# Create a mock conversation history
conversation_history = [
    {
        "type": "user_message",
        "text": "What does 'kippu' mean?",
        "timestamp": "2023-05-01T12:00:00",
        "intent": "vocabulary_help",
        "entities": {"word": "kippu"}
    },
    {
        "type": "assistant_message",
        "text": "'Kippu' (切符) means 'ticket' in Japanese. It's an important word to know when traveling by train.",
        "timestamp": "2023-05-01T12:00:30",
    },
    {
        "type": "user_message",
        "text": "How do I ask for a ticket to Odawara?",
        "timestamp": "2023-05-01T12:01:00",
        "intent": "translation_confirmation",
        "entities": {"destination": "Odawara", "word": "kippu"}
    },
    {
        "type": "assistant_message",
        "text": "You can say 'Odawara made no kippu o kudasai'. This literally means 'Please give me a ticket to Odawara'.",
        "timestamp": "2023-05-01T12:01:30",
    }
]

# Create a mock request
request = ClassifiedRequest(
    request_id="example-request",
    player_input="Can you tell me more about train tickets?",
    request_type="general",
    intent=IntentCategory.GENERAL_HINT,
    complexity=ComplexityLevel.COMPLEX,
    processing_tier=ProcessingTier.TIER_3,
    timestamp=datetime.now(),
    confidence=0.9,
    extracted_entities={"topic": "train tickets"}
)

# Create the conversation manager
manager = ConversationManager()

# Generate a prompt with conversation history
base_prompt = "You are Hachiko, a helpful companion dog who assists travelers in Japan."
state = ConversationState.FOLLOW_UP
prompt = manager.generate_contextual_prompt(request, conversation_history, state, base_prompt)

# Print the prompt
print("\nGenerated Prompt with OpenAI Conversation Format:\n")
print("-" * 80)
print(prompt)
print("-" * 80) 