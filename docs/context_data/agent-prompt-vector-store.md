# TDD Implementation Prompt for Tokyo Train Adventure Vector Database Integration

## Task Overview
Implement a vector database integration for the Tokyo Train Station Adventure game using Chroma DB to provide contextual information to LLMs from the tokyo-train-knowledge-base.json file.

## Implementation Approach (Test-Driven Development)
1. First write tests for the TokyoKnowledgeStore class that will interface with Chroma DB
1. Implement the class to pass the tests
1. Write tests for the integration with PromptManager
1. Implement the integration to pass the tests

### Step 1: Test the TokyoKnowledgeStore Class
- Test initialization with both ephemeral and persistent storage
- Test loading data from the knowledge base file
- Test document retrieval with different query types
- Test filtering by metadata
- Test contextual search based on game state

### Step 2: Implement TokyoKnowledgeStore
- Use Chroma DB as the underlying vector database
- Create a dedicated loader for the knowledge base format
- Implement filtering by document type, importance, etc.
- Add context-aware searching that prioritizes relevant information

### Step 3: Test PromptManager Integration
- Test generating prompts with knowledge base context
- Test integration with conversation history
- Test context prioritization based on request attributes

### Step 4: Implement PromptManager Extensions
- Extend the existing PromptManager to use the TokyoKnowledgeStore
- Add methods to incorporate contextual information in prompts
- Balance inclusion of conversation history and game world knowledge

### Expected Results
1. A TokyoKnowledgeStore class that efficiently stores and retrieves context from the knowledge base
1. Enhanced prompts that include relevant vocabulary, grammar, and game world information
1. More accurate and helpful responses from the LLM based on contextual awareness

### Acceptance Criteria
- All tests pass successfully
- Prompts include relevant information from the knowledge base
- System correctly prioritizes information based on request context
- Memory usage remains reasonable when loading the full knowledge base