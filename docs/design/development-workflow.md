# Development Workflow

This document outlines the development workflow used for the Tokyo Train Station Adventure project, with a specific focus on the companion AI system. We follow a Test-Driven Development (TDD) approach to ensure high-quality, well-tested code.

## Test-Driven Development (TDD) Workflow

Our development process follows these steps:

1. **Write Tests First**
   - Begin by writing tests that define the expected behavior of a component
   - Tests should fail initially (since the implementation doesn't exist yet)
   - Tests serve as both documentation and validation of requirements
   - Focus on covering all expected behaviors, edge cases, and error conditions

2. **Implement Minimal Code**
   - Write the minimal code needed to make the tests pass
   - Focus on functionality rather than optimization at this stage
   - Ensure the implementation satisfies all requirements defined in the tests
   - Avoid implementing features not covered by tests

3. **Refactor**
   - Once tests are passing, refactor the code to improve its structure
   - Maintain test coverage during refactoring to ensure functionality isn't broken
   - Improve code quality, readability, and performance
   - Apply design patterns and best practices where appropriate

4. **Update Project Plan**
   - Mark completed tasks in the implementation plan
   - Document any deviations from the original plan
   - Update task estimates for remaining work if necessary
   - This provides a clear record of progress and what remains to be done

5. **Create Commit**
   - Write a descriptive commit message that explains what was implemented
   - Reference the task ID from the implementation plan
   - Include key components and benefits of the implementation
   - Keep commits focused on specific tasks or features

## Testing Principles

Our testing approach is guided by these principles:

- **Isolation**: Each test should focus on a single unit of functionality
- **Independence**: Tests should not depend on each other or external state
- **Mocking**: External dependencies should be mocked to ensure tests are:
  - Fast: No waiting for external services
  - Reliable: Not affected by network issues or service changes
  - Controllable: Can simulate various responses including errors
  - Self-contained: Can run in any environment
- **Coverage**: Aim for high test coverage, especially for core functionality
- **Readability**: Tests should be clear about what they're testing and why

## Test Structure

We structure our tests using the Arrange-Act-Assert pattern:

1. **Arrange**: Set up the test conditions and inputs
2. **Act**: Execute the code being tested
3. **Assert**: Verify the results match expectations

Example:
```python
def test_grammar_explanation_handler():
    # Arrange
    handler = GrammarExplanationHandler()
    request = ClassifiedRequest(
        intent=IntentCategory.GRAMMAR_EXPLANATION,
        player_input="Can you explain は vs が?"
    )
    
    # Act
    prompt = handler.create_prompt(request)
    
    # Assert
    assert "grammar point" in prompt
    assert "は vs が" in prompt
    assert "JLPT N5" in prompt
```

## Commit Message Format

Our commit messages follow this format:

```
feat(component): Short description of what was implemented (Task ID)

Longer description explaining the key components, changes, and benefits.
Include any important implementation details or design decisions.

- Bullet points for specific changes
- Another specific change
```

Example:
```
feat(ai): Implement specialized handlers for complex scenarios (Task 4.2.1)

This commit implements specialized handlers for complex scenarios in Tier 3 
of the companion AI system, providing tailored prompt engineering and response 
processing for different types of complex requests.

- Created SpecializedHandler abstract base class
- Implemented DefaultHandler, GrammarExplanationHandler, TranslationHandler
- Added SpecializedHandlerRegistry for handler management
- Integrated handlers with Tier3Processor
```

## Code Review Process

Before merging code:

1. Ensure all tests pass
2. Verify code meets our style guidelines
3. Check that the implementation matches the requirements
4. Confirm the project plan has been updated
5. Review documentation for completeness and accuracy

## Continuous Integration

We use continuous integration to:

1. Run tests automatically on each commit
2. Verify code quality and style
3. Generate test coverage reports
4. Build and deploy to testing environments

This workflow ensures we build a robust, well-tested system with clear documentation of our progress through the implementation plan. 