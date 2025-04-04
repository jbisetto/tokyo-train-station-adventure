import asyncio
import logging
import json
import datetime
from src.ai.companion.core.models import CompanionRequest
from src.ai.companion.tier3.bedrock_client import BedrockClient, BedrockError

# Set up logging
logging.basicConfig(level=logging.DEBUG)

async def test_bedrock():
    """Test the BedrockClient with a simple request."""
    print("Running Bedrock test...")
    
    try:
        # Create a BedrockClient
        print("Creating BedrockClient...")
        client = BedrockClient(model_id="amazon.nova-micro-v1:0")
        
        # Create a test request
        print("Creating test request...")
        request = CompanionRequest(
            request_id="test-request",
            player_input="What does 'konnichiwa' mean?",
            request_type="language_help",
            timestamp=datetime.datetime(2025, 3, 19, 12, 0, 0)
        )
        
        # Debug: Add a hook to print raw API response
        original_call_bedrock_api = client._call_bedrock_api
        
        async def debug_call_bedrock_api(*args, **kwargs):
            try:
                raw_response = await original_call_bedrock_api(*args, **kwargs)
                print("\nRAW API RESPONSE:")
                print(json.dumps(raw_response, indent=2))
                return raw_response
            except Exception as e:
                print(f"Error in API call: {e}")
                raise
        
        # Replace the method with our debug version
        client._call_bedrock_api = debug_call_bedrock_api
        
        # Generate a response
        print("Generating response...")
        response = await client.generate(request)
        
        # Print the response
        print("\nResponse from Bedrock API:")
        print(response)
        print("\nTest successful!")
        
    except BedrockError as e:
        print(f"Error: {str(e)}")
        print("Test failed")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print("Test failed")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_bedrock()) 