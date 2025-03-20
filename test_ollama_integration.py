import logging
import asyncio
from ollama_client import OllamaClient

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests directly (without pytest) if executed as a script
    async def run_tests():
        print("=== Running Ollama Integration Tests ===")
        
        # Manual implementation of the test_config fixture
        tier2_config = get_config('tier2', {})
        ollama_config = tier2_config.get('ollama', {})
        config = {
            "base_url": ollama_config.get("base_url", "http://localhost:11434"),
            "default_model": ollama_config.get("default_model", "deepseek-r1:latest"),
            "temperature": ollama_config.get("temperature", 0.7),
            "max_tokens": ollama_config.get("max_tokens", 500),
        }
        
        # Manual implementation of the client fixture
        client_instance = OllamaClient(
            base_url=config["base_url"],
            default_model=config["default_model"],
            cache_enabled=False  # Disable cache for testing
        )
        
        try:
            print("\n== Testing Ollama Connectivity ==")
            await test_ollama_connectivity(client_instance, config)
            
            print("\n== Testing Simple Generation ==")
            await test_simple_generation(client_instance, config)
            
            print("\n== Testing Request Format ==")
            await test_request_format(client_instance, config)
            
            print("\n== Testing Direct API Call ==")
            await test_direct_api_call(config)
            
            print("\n=== All tests completed ===")
        except Exception as e:
            print(f"\n=== Test failed with error: {str(e)} ===")
            import traceback
            traceback.print_exc()
    
    # Run the tests
    asyncio.run(run_tests()) 