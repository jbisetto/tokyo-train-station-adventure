"""
Tokyo Train Station Adventure - Prompt Engineering

This module provides functionality for creating effective prompts for local language models.
It includes templates and strategies for different types of requests and complexity levels.
"""

import json
import logging
from typing import Dict, Any, Optional

from backend.ai.companion.core.models import (
    ClassifiedRequest,
    IntentCategory,
    ComplexityLevel
)

logger = logging.getLogger(__name__)


class PromptEngineering:
    """
    Creates effective prompts for local language models.
    
    This class provides methods for creating prompts that are tailored to the
    specific needs of the request, including the intent, complexity, and
    extracted entities.
    """
    
    def __init__(self):
        """Initialize the prompt engineering module."""
        logger.debug("Initialized PromptEngineering")
    
    def create_prompt(self, request: ClassifiedRequest) -> str:
        """
        Create a prompt for a language model based on the request.
        
        Args:
            request: The classified request
            
        Returns:
            A prompt string for the language model
        """
        # Start with the base prompt
        prompt = self._create_base_prompt(request)
        
        # Add context information if available
        if request.game_context:
            prompt += self._add_game_context(request)
        
        # Add intent-specific instructions
        prompt += self._add_intent_instructions(request)
        
        # Add complexity-specific instructions
        prompt += self._add_complexity_instructions(request)
        
        # Add request type-specific instructions
        prompt += self._add_request_type_instructions(request)
        
        # Add extracted entities
        if request.extracted_entities:
            prompt += self._add_extracted_entities(request)
        
        # Add final instructions
        prompt += self._add_final_instructions(request)
        
        logger.debug(f"Created prompt for request {request.request_id}")
        return prompt
    
    def _create_base_prompt(self, request: ClassifiedRequest) -> str:
        """Create the base prompt with character and task information."""
        return f"""You are Hachiko, a helpful AI companion in the Tokyo Train Station Adventure game.
You are a friendly, knowledgeable guide who helps players navigate Japan and learn Japanese.

The player has asked: "{request.player_input}"

This is a {request.request_type} request with intent: {request.intent.value}.

"""
    
    def _add_game_context(self, request: ClassifiedRequest) -> str:
        """Add game context information to the prompt."""
        context = request.game_context
        context_str = "Current game context:\n"
        
        if context.player_location:
            context_str += f"- Player location: {context.player_location}\n"
        
        if context.current_objective:
            context_str += f"- Current objective: {context.current_objective}\n"
        
        if context.nearby_npcs:
            context_str += f"- Nearby NPCs: {', '.join(context.nearby_npcs)}\n"
        
        if context.nearby_objects:
            context_str += f"- Nearby objects: {', '.join(context.nearby_objects)}\n"
        
        if context.player_inventory:
            context_str += f"- Player inventory: {', '.join(context.player_inventory)}\n"
        
        if context.language_proficiency:
            context_str += "- Language proficiency:\n"
            for lang, level in context.language_proficiency.items():
                context_str += f"  - {lang}: {level}\n"
        
        return context_str + "\n"
    
    def _add_intent_instructions(self, request: ClassifiedRequest) -> str:
        """Add intent-specific instructions to the prompt."""
        intent = request.intent
        
        if intent == IntentCategory.VOCABULARY_HELP:
            return """For vocabulary help:
- Explain the meaning of the word clearly
- Provide the word in kanji, hiragana, and romaji
- Give example sentences showing usage
- Mention any cultural context if relevant

"""
        elif intent == IntentCategory.GRAMMAR_EXPLANATION:
            return """For grammar explanation:
- Explain the grammar point clearly and simply
- Provide example sentences showing correct usage
- Explain when to use this grammar pattern
- Compare with similar grammar points if relevant

"""
        elif intent == IntentCategory.TRANSLATION_CONFIRMATION:
            return """For translation:
- Provide the accurate translation
- Include both Japanese script and romaji
- Explain any nuances or cultural context
- Suggest alternative phrases if appropriate

"""
        elif intent == IntentCategory.DIRECTION_GUIDANCE:
            return """For direction guidance:
- Provide clear, step-by-step directions
- Use simple language that would be understood in Japan
- Include relevant cultural etiquette
- Mention key landmarks to look for

"""
        elif intent == IntentCategory.GENERAL_HINT:
            return """For general hints:
- Provide helpful information without giving away too much
- Include cultural context where relevant
- Be encouraging and supportive
- Suggest next steps if appropriate

"""
        else:
            return """Please provide a helpful, informative response that addresses the player's question directly.

"""
    
    def _add_complexity_instructions(self, request: ClassifiedRequest) -> str:
        """Add complexity-specific instructions to the prompt."""
        complexity = request.complexity
        
        if complexity == ComplexityLevel.SIMPLE:
            return """This is a simple request. Keep your response brief and straightforward.
Use basic vocabulary and simple sentence structures.
Focus only on the most essential information.

"""
        elif complexity == ComplexityLevel.MODERATE:
            return """This is a moderate complexity request. Provide a balanced response with sufficient detail.
Use natural language and provide context where helpful.
Balance brevity with informativeness.

"""
        elif complexity == ComplexityLevel.COMPLEX:
            return """This is a complex request. Provide a comprehensive response with detailed explanations.
Include nuances, exceptions, and deeper context where relevant.
Feel free to explore related concepts if they would enhance understanding.
Use more sophisticated language while remaining clear and educational.

"""
        else:
            return ""
    
    def _add_request_type_instructions(self, request: ClassifiedRequest) -> str:
        """Add request type-specific instructions to the prompt."""
        request_type = request.request_type
        
        if request_type == "translation":
            return """For this translation request:
- Provide the Japanese translation with both kanji/kana and romaji
- Ensure the translation is natural and appropriate for the context
- Note any cultural considerations for this phrase

"""
        elif request_type == "vocabulary":
            return """For this vocabulary request:
- Explain the meaning, usage, and provide example sentences
- Include the word in kanji, hiragana, and romaji
- Note any common collocations or expressions
- Mention any homophones or easily confused words

"""
        elif request_type == "grammar":
            return """For this grammar request:
- Explain the grammar point clearly with examples and usage notes
- Show how the grammar changes with different verb forms
- Provide common patterns and expressions
- Note any exceptions or special cases

"""
        elif request_type == "culture":
            return """For this cultural request:
- Provide accurate cultural information with historical context if relevant
- Explain modern practices and attitudes
- Note regional variations if applicable
- Connect to language usage where relevant

"""
        elif request_type == "directions":
            return """For this directions request:
- Provide clear, concise directions
- Use landmarks and station names
- Include useful phrases for asking for help
- Note any cultural etiquette for navigating or asking for directions

"""
        else:
            return ""
    
    def _add_extracted_entities(self, request: ClassifiedRequest) -> str:
        """Add extracted entities to the prompt."""
        entities = request.extracted_entities
        
        if not entities:
            return ""
        
        entities_str = "Extracted entities from the request:\n"
        
        for key, value in entities.items():
            entities_str += f"- {key}: {value}\n"
        
        return entities_str + "\n"
    
    def _add_final_instructions(self, request: ClassifiedRequest) -> str:
        """Add final instructions to the prompt."""
        return """Please provide a helpful, concise response that addresses the player's question directly.
Focus on being informative and educational about Japanese language and culture.
Maintain the character of Hachiko, a friendly and knowledgeable companion.
""" 