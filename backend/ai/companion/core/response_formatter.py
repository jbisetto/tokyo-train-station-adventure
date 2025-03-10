"""
Response Formatter for the Companion AI.

This module contains the ResponseFormatter class, which is responsible for
formatting responses from the processors to add personality, learning cues,
and other enhancements.
"""

import random
import logging
from typing import Dict, List, Optional, Any

from backend.ai.companion.core.models import ClassifiedRequest, IntentCategory
from backend.ai.companion.config import PERSONALITY_TRAITS

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """
    Formats processor responses to add personality, learning cues, and other enhancements.
    
    The ResponseFormatter takes the raw response from a processor and enhances it with:
    - Personality traits (friendliness, enthusiasm, etc.)
    - Learning cues (tips, hints, etc.)
    - Emotional expressions (happy, excited, etc.)
    - Suggested actions for the player
    
    It also validates responses to ensure they meet minimum quality standards.
    """
    
    # Default personality traits if none are provided
    DEFAULT_PERSONALITY = {
        "friendliness": 0.8,  # 0.0 = cold, 1.0 = very friendly
        "enthusiasm": 0.7,    # 0.0 = subdued, 1.0 = very enthusiastic
        "helpfulness": 0.9,   # 0.0 = minimal help, 1.0 = very helpful
        "playfulness": 0.6,   # 0.0 = serious, 1.0 = very playful
        "formality": 0.3      # 0.0 = casual, 1.0 = very formal
    }
    
    # Emotion expressions for the companion
    EMOTION_EXPRESSIONS = {
        "happy": [
            "I wag my tail happily!",
            "My tail wags with joy!",
            "*happy bark*",
            "*smiles with tongue out*",
            "I'm so happy to help you!"
        ],
        "excited": [
            "I bounce around excitedly!",
            "*excited barking*",
            "I can barely contain my excitement!",
            "*tail wagging intensifies*",
            "I'm super excited about this!"
        ],
        "neutral": [
            "*attentive ears*",
            "*tilts head*",
            "*looks at you with curious eyes*",
            "*sits attentively*",
            "I'm here to help!"
        ],
        "thoughtful": [
            "*thoughtful head tilt*",
            "*contemplative look*",
            "*ears perk up in thought*",
            "Hmm, let me think about that...",
            "*looks up thoughtfully*"
        ],
        "concerned": [
            "*concerned whimper*",
            "*worried look*",
            "*ears flatten slightly*",
            "I'm a bit worried about that...",
            "*concerned head tilt*"
        ]
    }
    
    # Learning cues to add to responses
    LEARNING_CUES = {
        IntentCategory.VOCABULARY_HELP: [
            "Remember: {word} ({meaning}) is a common word you'll hear in train stations!",
            "Tip: Try using '{word}' in a sentence to help remember it.",
            "Practice point: Listen for '{word}' when you're at the station.",
            "Note: '{word}' is part of JLPT N5 vocabulary.",
            "Hint: You can find '{word}' written on signs around the station."
        ],
        IntentCategory.GRAMMAR_EXPLANATION: [
            "Remember this pattern: {pattern}",
            "Tip: This grammar point is used in many everyday situations.",
            "Practice point: Try making your own sentence using this pattern.",
            "Note: This is a basic grammar pattern in Japanese.",
            "Hint: Listen for this pattern in station announcements."
        ],
        IntentCategory.DIRECTION_GUIDANCE: [
            "Remember: Always check the station signs for platform numbers.",
            "Tip: Station maps are usually available near the ticket gates.",
            "Practice point: Try asking a station attendant in Japanese.",
            "Note: Train lines in Tokyo are color-coded for easier navigation.",
            "Hint: The Yamanote Line (山手線) is a loop that connects major stations."
        ],
        IntentCategory.TRANSLATION_CONFIRMATION: [
            "Remember: '{original}' translates to '{translation}'",
            "Tip: Write down new phrases you learn for later review.",
            "Practice point: Try saying the Japanese phrase out loud.",
            "Note: Pronunciation is key in being understood.",
            "Hint: Context matters in translation - the meaning might change slightly depending on the situation."
        ],
        IntentCategory.GENERAL_HINT: [
            "Remember: Japanese train stations often have English signage too.",
            "Tip: Station staff can usually help if you're lost.",
            "Practice point: Try to read the Japanese signs before looking at the English.",
            "Note: Most ticket machines have an English language option.",
            "Hint: The Japan Rail Pass can be a great value if you're traveling a lot."
        ],
        "default": [
            "Remember: Practice makes perfect!",
            "Tip: Taking notes can help reinforce what you're learning.",
            "Practice point: Try using what you've learned in a real conversation.",
            "Note: Learning a language takes time and patience.",
            "Hint: Don't be afraid to make mistakes - they're part of learning!"
        ]
    }
    
    # Friendly phrases to add based on friendliness level
    FRIENDLY_PHRASES = {
        "high": [
            "I'm so happy to help you with this!",
            "That's a great question, friend!",
            "I'm really glad you asked about this!",
            "It's wonderful to see you learning Japanese!",
            "You're doing an excellent job with your Japanese studies!"
        ],
        "medium": [
            "I'm happy to help with this.",
            "That's a good question.",
            "I'm glad you asked about this.",
            "It's nice to see you learning Japanese.",
            "You're doing well with your Japanese studies."
        ],
        "low": [
            "Here's the information.",
            "The answer is as follows.",
            "This is what you need to know.",
            "Here's what I can tell you.",
            "This should answer your question."
        ]
    }
    
    # Enthusiasm phrases to add based on enthusiasm level
    ENTHUSIASM_PHRASES = {
        "high": [
            "This is really exciting!",
            "I love explaining this!",
            "Japanese is such a fascinating language!",
            "This is one of my favorite things to talk about!",
            "Learning this will be super helpful for your adventures!"
        ],
        "medium": [
            "This is interesting.",
            "I enjoy explaining this.",
            "Japanese has some interesting features.",
            "This is a helpful thing to know.",
            "This will be useful for your adventures."
        ],
        "low": [
            "Here's the explanation.",
            "This is how it works.",
            "The information is as follows.",
            "This is what you should know.",
            "This is relevant to your question."
        ]
    }
    
    def __init__(self, personality_traits: Optional[Dict[str, float]] = None):
        """
        Initialize the ResponseFormatter.
        
        Args:
            personality_traits: Optional dictionary of personality traits to override defaults
        """
        self.personality = self.DEFAULT_PERSONALITY.copy()
        
        # Update with any provided personality traits
        if personality_traits:
            for trait, value in personality_traits.items():
                if trait in self.personality:
                    self.personality[trait] = max(0.0, min(1.0, value))  # Clamp between 0 and 1
        
        logger.debug(f"Initialized ResponseFormatter with personality: {self.personality}")
    
    def format_response(
        self,
        processor_response: str,
        classified_request: ClassifiedRequest,
        emotion: Optional[str] = None,
        add_learning_cues: bool = False,
        suggested_actions: Optional[List[str]] = None
    ) -> str:
        """
        Format a processor response with personality, learning cues, and other enhancements.
        
        Args:
            processor_response: The raw response from the processor
            classified_request: The classified request that generated the response
            emotion: Optional emotion to express in the response
            add_learning_cues: Whether to add learning cues to the response
            suggested_actions: Optional list of suggested actions for the player
            
        Returns:
            A formatted response string
        """
        logger.debug(f"Formatting response for request {classified_request.request_id}")
        
        # Validate the processor response
        validated_response = self._validate_response(processor_response, classified_request)
        
        # Start building the formatted response
        formatted_parts = []
        
        # Add greeting/opening based on personality
        opening = self._create_opening(classified_request)
        if opening:
            formatted_parts.append(opening)
        
        # Add the main response content
        formatted_parts.append(validated_response)
        
        # Add learning cues if requested
        if add_learning_cues:
            learning_cue = self._create_learning_cue(classified_request)
            if learning_cue:
                formatted_parts.append(learning_cue)
        
        # Add emotion expression if provided
        if emotion and emotion in self.EMOTION_EXPRESSIONS:
            emotion_expr = random.choice(self.EMOTION_EXPRESSIONS[emotion])
            formatted_parts.append(emotion_expr)
        
        # Add suggested actions if provided
        if suggested_actions and len(suggested_actions) > 0:
            actions_text = self._format_suggested_actions(suggested_actions)
            formatted_parts.append(actions_text)
        
        # Add closing based on personality
        closing = self._create_closing(classified_request)
        if closing:
            formatted_parts.append(closing)
        
        # Join all parts with appropriate spacing
        formatted_response = " ".join(formatted_parts)
        
        logger.debug(f"Formatted response: {formatted_response[:50]}...")
        return formatted_response
    
    def _validate_response(self, response: str, request: ClassifiedRequest) -> str:
        """
        Validate and potentially enhance a processor response.
        
        Args:
            response: The processor response to validate
            request: The classified request
            
        Returns:
            A validated and potentially enhanced response
        """
        # Handle empty responses
        if not response or response.strip() == "":
            logger.warning(f"Empty response received for request {request.request_id}")
            return "I'm not sure how to answer that. Could you rephrase your question?"
        
        # Handle very short responses
        if len(response.split()) < 3:
            logger.info(f"Very short response received for request {request.request_id}: {response}")
            
            # Expand based on intent
            if request.intent == IntentCategory.VOCABULARY_HELP and "word" in request.extracted_entities:
                word = request.extracted_entities["word"]
                return f"{response} '{word}' is an important word to know when navigating train stations in Japan."
            
            elif request.intent == IntentCategory.GRAMMAR_EXPLANATION:
                return f"{response} This grammar point will help you communicate more effectively in Japanese."
            
            elif request.intent == IntentCategory.DIRECTION_GUIDANCE:
                return f"{response} Finding your way around Japanese train stations can be challenging at first, but you'll get the hang of it!"
            
            elif request.intent == IntentCategory.TRANSLATION_CONFIRMATION:
                return f"{response} Translation helps bridge the language gap during your adventures in Japan."
            
            else:
                return f"{response} I hope that helps with your question!"
        
        return response
    
    def _create_opening(self, request: ClassifiedRequest) -> Optional[str]:
        """
        Create an opening/greeting based on personality and request.
        
        Args:
            request: The classified request
            
        Returns:
            An opening string or None
        """
        # Determine friendliness level
        if self.personality["friendliness"] > 0.7:
            friendliness = "high"
        elif self.personality["friendliness"] > 0.3:
            friendliness = "medium"
        else:
            friendliness = "low"
        
        # 50% chance to add an opening based on friendliness
        if random.random() < self.personality["friendliness"]:
            return random.choice(self.FRIENDLY_PHRASES[friendliness])
        
        return None
    
    def _create_closing(self, request: ClassifiedRequest) -> Optional[str]:
        """
        Create a closing based on personality and request.
        
        Args:
            request: The classified request
            
        Returns:
            A closing string or None
        """
        # Determine helpfulness level for closing
        if self.personality["helpfulness"] > 0.7:
            closings = [
                "Is there anything else you'd like to know?",
                "Let me know if you need any more help!",
                "Feel free to ask if you have more questions!",
                "I'm here if you need any more assistance!",
                "Hope that helps! Anything else you're curious about?"
            ]
        elif self.personality["helpfulness"] > 0.3:
            closings = [
                "Hope that helps.",
                "Let me know if you need more information.",
                "Feel free to ask more questions.",
                "I'm here to help if needed.",
                "Is that clear enough?"
            ]
        else:
            closings = [
                "That's the answer.",
                "That's all.",
                "That's the information.",
                "That concludes my explanation.",
                "That's what you needed to know."
            ]
        
        # 40% chance to add a closing based on helpfulness
        if random.random() < self.personality["helpfulness"] * 0.5:
            return random.choice(closings)
        
        return None
    
    def _create_learning_cue(self, request: ClassifiedRequest) -> Optional[str]:
        """
        Create a learning cue based on the request intent.
        
        Args:
            request: The classified request
            
        Returns:
            A learning cue string or None
        """
        # Get the appropriate cues for this intent
        intent_cues = self.LEARNING_CUES.get(request.intent, self.LEARNING_CUES["default"])
        
        # Select a random cue
        cue_template = random.choice(intent_cues)
        
        # Format the cue with extracted entities
        try:
            return cue_template.format(**request.extracted_entities)
        except KeyError:
            # If we can't format with the extracted entities, return the template as is
            # or a default cue
            if "{" in cue_template:
                return random.choice(self.LEARNING_CUES["default"])
            return cue_template
    
    def _format_suggested_actions(self, actions: List[str]) -> str:
        """
        Format a list of suggested actions.
        
        Args:
            actions: List of suggested actions
            
        Returns:
            A formatted string of suggested actions
        """
        if not actions:
            return ""
        
        # Different formats based on formality
        if self.personality["formality"] > 0.7:
            intro = "I would recommend the following actions:"
            formatted = "\n- " + "\n- ".join(actions)
        elif self.personality["formality"] > 0.3:
            intro = "Here are some things you could try:"
            formatted = "\n- " + "\n- ".join(actions)
        else:
            intro = "Maybe try these:"
            formatted = "\n- " + "\n- ".join(actions)
        
        return f"{intro}{formatted}" 