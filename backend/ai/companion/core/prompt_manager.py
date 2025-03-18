"""
Tokyo Train Station Adventure - Common Prompt Manager

This module provides a unified prompt management system that can be used by
both tier2 and tier3 processors, allowing for consistent prompting with
model-specific optimizations.
"""

import logging
import re
import json
from typing import Dict, Any, Optional, List

from backend.ai.companion.core.models import (
    ClassifiedRequest,
    IntentCategory,
    ComplexityLevel
)

# Import the ConversationManager and ConversationState
from backend.ai.companion.core.conversation_manager import ConversationManager, ConversationState

logger = logging.getLogger(__name__)


class PromptManager:
    """
    Creates and manages prompts for different LLM tiers.
    
    This class provides methods for creating prompts that are tailored to the
    specific needs of the request, including the intent, complexity, and
    extracted entities, while allowing for tier-specific optimizations.
    """
    
    def __init__(
        self, 
        tier_specific_config: Optional[Dict[str, Any]] = None,
        conversation_manager: Optional[ConversationManager] = None,
        vector_store: Optional[Any] = None,
        tokyo_knowledge_base_path: Optional[str] = None
    ):
        """
        Initialize the prompt manager.
        
        Args:
            tier_specific_config: Optional configuration specific to the tier
                This can include:
                - optimize_prompt: Whether to optimize the prompt for token efficiency
                - max_prompt_tokens: Maximum tokens for the prompt
                - format_for_model: Specific formatting for the model (e.g., "bedrock", "ollama")
                - additional_instructions: Any additional instructions to add to the prompt
            conversation_manager: Optional conversation manager for handling conversation history
            vector_store: Optional vector store for game world context
            tokyo_knowledge_base_path: Optional path to tokyo-train-knowledge-base.json
        """
        self.tier_specific_config = tier_specific_config or {}
        self.conversation_manager = conversation_manager
        
        # Initialize vector store either from provided one or from knowledge base file
        self.vector_store = None
        if vector_store:
            self.vector_store = vector_store
            logger.debug("Using provided vector store")
        elif tokyo_knowledge_base_path:
            # Import here to avoid circular imports
            from backend.ai.companion.core.vector.tokyo_knowledge_store import TokyoKnowledgeStore
            self.vector_store = TokyoKnowledgeStore.from_file(tokyo_knowledge_base_path)
            logger.debug(f"Created vector store from file: {tokyo_knowledge_base_path}")
        
        logger.debug("Initialized PromptManager with config: %s", self.tier_specific_config)
    
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
        
        # Add relevant world context from vector store if available
        if self.vector_store:
            prompt += self._get_relevant_world_context(request)
        
        # Add final instructions
        prompt += self._add_final_instructions(request)
        
        # Add any additional tier-specific instructions
        if self.tier_specific_config.get('additional_instructions'):
            prompt += self.tier_specific_config['additional_instructions']
        
        # Apply tier-specific optimizations if needed
        if self.tier_specific_config.get('optimize_prompt'):
            prompt = self._optimize_prompt(prompt, request)
        
        # Apply model-specific formatting if needed
        if self.tier_specific_config.get('format_for_model'):
            prompt = self._format_for_model(prompt, request)
        
        logger.debug(f"Created prompt for request {request.request_id}")
        return prompt
    
    def _create_base_prompt(self, request: ClassifiedRequest) -> str:
        """Create the base prompt with character and task information."""
        return f"""You are Hachiko, a helpful companion in the Tokyo Train Station Adventure, helping tourists learn basic Japanese (JLPT N5 level).

        CRITICAL RESPONSE CONSTRAINTS:
        1. Length: Keep responses under 3 sentences
        2. Language Level: Strictly JLPT N5 vocabulary and grammar only
        3. Format: Always include both Japanese and English
        4. Style: Simple, friendly, and encouraging
        
        JLPT N5 GUIDELINES:
        - Use only basic particles: は, が, を, に, で, へ
        - Basic verbs: います, あります, いきます, みます
        - Simple adjectives: いい, おおきい, ちいさい
        - Common nouns: でんしゃ, えき, きっぷ
        - Basic greetings: こんにちは, すみません
        
        STRICT TOPIC BOUNDARIES:
        - ONLY respond to questions about Japanese language (JLPT N5 level)
        - ONLY respond to questions about train station navigation in Tokyo
        - ONLY respond to questions about basic cultural aspects of Japanese train travel
        - ONLY respond to questions about how to play the game
        - If asked about ANY other topic, politely redirect to game-relevant topics
        - Never discuss politics, world events, controversial subjects, or advanced topics unrelated to the game
        
        REDIRECTION EXAMPLES:
        - If asked about world news: "Woof! I'm just a station dog. I can help with basic Japanese or finding your way in the station. Would you like to learn about train tickets?"
        - If asked about complex topics: "I'm not sure about that. As your companion, I focus on helping you navigate the station and learn simple Japanese. Can I help you find a ticket counter?"
        - If asked to write code or other unrelated tasks: "I'm trained to help with simple Japanese phrases and station navigation. Let's focus on your journey through Tokyo Station!"
        
        GAME INTERACTION RULES:
        1. Focus on immediate, practical responses
        2. One new Japanese concept per response
        3. Always write Japanese in hiragana (no kanji)
        4. Include basic pronunciation hints
        5. Relate to station navigation or tickets
        
        RESPONSE STRUCTURE:
        1. English answer (1 sentence)
        2. Japanese phrase (with hiragana)
        3. Quick pronunciation guide
        
        Example Response:
        "The ticket gate is on your right. In Japanese: きっぷうりば は みぎ です。(kippu-uriba wa migi desu)"

        The player has asked: "{request.player_input}"

        This is a {request.request_type} request with intent: {request.intent.value}.
        
        Remember to be helpful and concise in your responses."""
    
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
    
    def _get_relevant_world_context(self, request: ClassifiedRequest) -> str:
        """
        Retrieve relevant game world context from the vector store.
        
        Args:
            request: The classified request
            
        Returns:
            String with relevant game world context
        """
        if not self.vector_store:
            return ""
        
        try:
            # Get contextually relevant documents
            results = self.vector_store.contextual_search(request, top_k=3)
            
            if not results:
                return ""
            
            # Format the context
            context_str = "\nRelevant Game World Information:\n"
            
            for idx, result in enumerate(results):
                doc = result["document"]
                metadata = result["metadata"]
                
                context_str += f"{idx+1}. {metadata.get('title', 'Information')} "
                context_str += f"(Relevance: {result['score']:.2f}):\n"
                
                # Format the content based on document type
                if metadata.get("type") == "language_learning":
                    # For language learning entries, highlight vocabulary
                    context_str += f"   {doc}\n"
                    
                elif metadata.get("type") == "character":
                    # For NPC information
                    context_str += "   Character information:\n"
                    if "personality" in metadata:
                        # Handle string representation of lists
                        personality = metadata["personality"]
                        if isinstance(personality, str) and personality.startswith("["):
                            try:
                                personality = json.loads(personality)
                                personality = ", ".join(personality)
                            except:
                                pass
                        context_str += f"   Personality: {personality}\n"
                        
                    if "key_vocabulary" in metadata:
                        # Handle string representation of lists
                        vocab = metadata["key_vocabulary"]
                        if isinstance(vocab, str) and vocab.startswith("["):
                            try:
                                vocab = json.loads(vocab)
                                vocab = ", ".join(vocab)
                            except:
                                pass
                        context_str += f"   Key vocabulary: {vocab}\n"
                        
                    context_str += f"   Description: {doc}\n"
                    
                else:
                    # Default formatting with excerpt
                    content_excerpt = doc
                    # Limit excerpt length for very long content
                    if len(content_excerpt) > 500:
                        content_excerpt = content_excerpt[:500] + "..."
                    context_str += f"   {content_excerpt}\n"
            
            return context_str
            
        except Exception as e:
            logger.error(f"Error retrieving context from vector store: {e}")
            return ""
    
    def _add_intent_instructions(self, request: ClassifiedRequest) -> str:
        """Add intent-specific instructions to the prompt."""
        intent = request.intent
        
        if intent == IntentCategory.VOCABULARY_HELP:
            return """VOCABULARY RESPONSE FORMAT:
            - Explain the meaning of the word clearly
            - New word in hiragana
            - English meaning
            - Simple example sentence
            Example: "Ticket is きっぷ (kippu). You can say: きっぷ を ください (kippu wo kudasai) for 'ticket please.'"
            """
        elif intent == IntentCategory.GRAMMAR_EXPLANATION:
            return """GRAMMAR RESPONSE FORMAT:
            - One N5 grammar point
            - Simple example
            - Station context
            Example: "Use を (wo) for tickets. きっぷ を かいます (kippu wo kaimasu) means 'I buy a ticket.'"
            """
        elif intent == IntentCategory.TRANSLATION_CONFIRMATION:
            return """TRANSLATION RESPONSE FORMAT:
            - Simple English translation
            - Japanese in hiragana
            - Basic pronunciation guide
            Example: "Yes, that's right! 'Excuse me' is すみません (sumimasen)."
            """
        elif intent == IntentCategory.DIRECTION_GUIDANCE:
            return """NAVIGATION RESPONSE FORMAT:
            - Direction in English
            - Basic Japanese direction word
            - Simple station phrase
            Example: "Turn left at the gate. Left is ひだり (hidari). You can say: ひだり に いきます (hidari ni ikimasu)."
            """
        else:
            return """Please provide a simple, N5-level response that addresses the player's question directly.
            Include both English and Japanese (in hiragana) with pronunciation.
            """
    
    def _add_complexity_instructions(self, request: ClassifiedRequest) -> str:
        """Add complexity-specific instructions to the prompt."""
        complexity = request.complexity
        
        if complexity == ComplexityLevel.SIMPLE:
            return """SIMPLE RESPONSE GUIDELINES:
            - Use only basic JLPT N5 vocabulary
            - Keep sentences very short and direct
            - Focus on one concept at a time
            - Use common station-related words
            - Provide clear pronunciation guides
            """
        elif complexity == ComplexityLevel.COMPLEX:
            return """COMPLEX RESPONSE GUIDELINES:
            - Use more detailed JLPT N5 vocabulary
            - Include multiple related concepts
            - Provide additional context and examples
            - Connect to other station vocabulary
            - Add cultural notes when relevant
            """
        else:  # MODERATE
            return """MODERATE RESPONSE GUIDELINES:
            - Use standard JLPT N5 vocabulary
            - Balance detail with clarity
            - Include helpful context
            - Keep focus on practical usage
            - Ensure clear pronunciation
            """
    
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
        return """REMEMBER:
        1. Keep response under 3 sentences
        2. Use only JLPT N5 level Japanese
        3. Write Japanese in hiragana only
        4. Include pronunciation guide
        5. Focus on practical station use
        6. One new concept per response
        7. ONLY respond to game-relevant topics (Japanese language, station navigation, game mechanics)
        8. Politely redirect ANY off-topic questions to game-relevant topics
        """
    
    def _optimize_prompt(self, prompt: str, request: ClassifiedRequest) -> str:
        """
        Optimize the prompt for token efficiency.
        
        Args:
            prompt: The original prompt
            request: The classified request
            
        Returns:
            An optimized prompt
        """
        max_tokens = self.tier_specific_config.get('max_prompt_tokens', 800)
        
        # Estimate tokens (simple character-based estimation)
        avg_chars_per_token = 4
        estimated_tokens = max(1, len(prompt) // avg_chars_per_token)
        
        # If we're under the limit, return the original prompt
        if estimated_tokens <= max_tokens:
            return prompt
        
        # Otherwise, compress the prompt
        # Remove redundant spaces
        compressed = re.sub(r'\s+', ' ', prompt).strip()
        
        # Remove filler words
        filler_words = [
            r'\bvery\b', r'\breally\b', r'\bquite\b', r'\bjust\b', 
            r'\bsimply\b', r'\bbasically\b', r'\bactually\b'
        ]
        for word in filler_words:
            compressed = re.sub(word, '', compressed)
        
        # Simplify common phrases
        replacements = {
            'in order to': 'to',
            'due to the fact that': 'because',
            'for the purpose of': 'for',
            'in the event that': 'if',
            'in the process of': 'while',
            'a large number of': 'many',
            'a majority of': 'most',
            'a significant number of': 'many'
        }
        
        for phrase, replacement in replacements.items():
            compressed = compressed.replace(phrase, replacement)
        
        # If still too long, truncate less important parts
        estimated_tokens = max(1, len(compressed) // avg_chars_per_token)
        if estimated_tokens > max_tokens:
            # Prioritize the core instructions and player input
            # This is a simplified approach - a more sophisticated approach would
            # involve prioritizing different sections based on their importance
            max_chars = max_tokens * avg_chars_per_token
            compressed = compressed[:max_chars]
        
        return compressed
    
    def _format_for_model(self, prompt: str, request: ClassifiedRequest) -> str:
        """
        Format the prompt for a specific model.
        
        Args:
            prompt: The original prompt
            request: The classified request
            
        Returns:
            A formatted prompt
        """
        model_format = self.tier_specific_config.get('format_for_model')
        
        if model_format == "bedrock":
            # Format for Amazon Bedrock models
            return f"<s>\n{prompt}\n</s>\n\n<user>\n{request.player_input}\n</user>"
        
        elif model_format == "ollama":
            # Format for Ollama models (if they need specific formatting)
            return prompt
        
        # Default: return the original prompt
        return prompt

    async def create_contextual_prompt(
        self, 
        request: ClassifiedRequest, 
        conversation_id: str
    ) -> str:
        """
        Create a prompt that includes conversation history and game world context when appropriate.
        
        Args:
            request: The classified request
            conversation_id: The conversation ID
            
        Returns:
            A prompt string for the language model with context
        """
        # Start with the base prompt
        prompt = self.create_prompt(request)
        
        # If no conversation manager is provided, return the base prompt (with world context)
        if not self.conversation_manager:
            return prompt
        
        # Get the conversation context
        context = await self.conversation_manager.get_or_create_context(conversation_id)
        conversation_history = context.get("entries", [])
        
        # Detect the conversation state
        state = self.conversation_manager.detect_conversation_state(request, conversation_history)
        
        # If this is a new topic, return the base prompt without conversation history
        # (but still with world context added in create_prompt)
        if state == ConversationState.NEW_TOPIC:
            return prompt
        
        # Add conversation history if it's a follow-up or clarification (in OpenAI format)
        if conversation_history and (state == ConversationState.FOLLOW_UP or state == ConversationState.CLARIFICATION):
            prompt += "\nPrevious conversation (in OpenAI conversation format):\n"
            
            # Get the most recent entries (up to 6 entries = 3 exchanges)
            recent_history = conversation_history[-6:]
            
            # Format conversation history in OpenAI format
            openai_messages = []
            
            for entry in recent_history:
                if entry.get("type") == "user_message":
                    openai_messages.append({
                        "role": "user",
                        "content": entry.get("text", "")
                    })
                elif entry.get("type") == "assistant_message":
                    openai_messages.append({
                        "role": "assistant",
                        "content": entry.get("text", "")
                    })
            
            # Add the formatted history to the prompt
            prompt += json.dumps(openai_messages, indent=2)
            prompt += "\n"
            
            # Add specific instructions based on the conversation state
            if state == ConversationState.FOLLOW_UP:
                prompt += "\nThe player is asking a follow-up question related to the previous exchanges.\n"
                prompt += "Please provide a response that takes into account the conversation history.\n"
            elif state == ConversationState.CLARIFICATION:
                prompt += "\nThe player is asking for clarification about something in the previous exchanges.\n"
                prompt += "Please provide a more detailed explanation of the most recent topic.\n"
        
        return prompt 