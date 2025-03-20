def format_response(self, response_data):
    # ... existing code ...
    
    # Get the processing tier from the response data, ensuring it's passed through correctly
    processing_tier = response_data.get('processing_tier', 'unknown')
    
    # Convert from enum to string if needed
    if hasattr(processing_tier, 'name'):
        processing_tier = processing_tier.name
    
    # ... existing code ...
    return f"Response details - dialogue length: {len(response_text)}, processing tier: {processing_tier}" 