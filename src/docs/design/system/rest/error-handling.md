# API Error Handling

This document outlines the error handling approach used in the Tokyo Train Station Adventure game's REST API.

## Error Response Structure

All error responses from the API follow a consistent format:

```json
{
  "error": "string",
  "message": "string",
  "details": "object|null"
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `error` | string | Error type identifier corresponding to HTTP status code |
| `message` | string | Human-readable description of the error |
| `details` | object | Additional information about the error (optional) |

## HTTP Status Codes

The API uses standard HTTP status codes to indicate the general category of error:

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | Bad Request | Request contains invalid data or is malformed |
| 401 | Unauthorized | Authentication is required or has failed |
| 403 | Forbidden | The client lacks permission for the requested operation |
| 404 | Not Found | The requested resource could not be found |
| 409 | Conflict | Request could not be completed due to a conflict with resource state |
| 422 | Unprocessable Entity | Request was well-formed but cannot be processed |
| 429 | Too Many Requests | Rate limit has been exceeded |
| 500 | Internal Server Error | An unexpected error occurred on the server |
| 503 | Service Unavailable | The service is temporarily unavailable |

## Detailed Error Patterns

### Validation Errors (400 Bad Request)

When a request fails validation, the `details` field contains specific information about which fields failed validation and why:

```json
{
  "error": "Bad Request",
  "message": "Invalid request format or missing required fields",
  "details": {
    "fieldErrors": [
      {
        "field": "playerId",
        "message": "Field is required"
      },
      {
        "field": "conversationParameters.temperatureDefault",
        "message": "Value must be between 0.0 and 1.0"
      }
    ]
  }
}
```

### Authentication Errors (401 Unauthorized)

Authentication errors include minimal details to avoid providing sensitive information:

```json
{
  "error": "Unauthorized",
  "message": "Authentication required to access this endpoint",
  "details": null
}
```

### Permission Errors (403 Forbidden)

Permission errors indicate that the authenticated user lacks the required permissions:

```json
{
  "error": "Forbidden",
  "message": "Admin role required to modify NPC configurations",
  "details": null
}
```

### Resource Not Found Errors (404 Not Found)

Not Found errors specify which resource could not be found:

```json
{
  "error": "Not Found",
  "message": "NPC with ID ticket_operator_2 not found",
  "details": null
}
```

### Conflict Errors (409 Conflict)

Conflict errors provide information about the conflicting state:

```json
{
  "error": "Conflict",
  "message": "NPC configuration was modified by another request",
  "details": {
    "lastModified": "2025-03-12T09:44:55Z"
  }
}
```

### Process Errors (422 Unprocessable Entity)

Used when the request itself is valid but cannot be processed due to semantic errors:

```json
{
  "error": "Unprocessable Entity",
  "message": "Unable to process dialogue input",
  "details": {
    "reason": "Language not supported"
  }
}
```

### Rate Limiting Errors (429 Too Many Requests)

Rate limiting errors include information about when the client can retry:

```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded",
  "details": {
    "retryAfter": 60,
    "limit": "100 requests per minute"
  }
}
```

### Server Errors (500 Internal Server Error)

Server errors provide minimal details to avoid exposing internal implementation details:

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred while processing the request",
  "details": null
}
```

## Error Handling Implementation

The API handles errors using a centralized exception handling system:

```python
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    field_errors = []
    for error in exc.errors():
        field_errors.append({
            "field": error["loc"][-1],
            "message": error["msg"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Bad Request",
            "message": "Invalid request format or missing required fields",
            "details": {
                "fieldErrors": field_errors
            }
        }
    )

@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "Unauthorized",
            "message": str(exc),
            "details": None
        }
    )

# Custom exception handlers for other error types...

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    # Log the exception for internal review
    logger.error(f"Unexpected error: {str(exc)}", exc_info=exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred while processing the request",
            "details": None
        }
    )
```

## Custom Exception Classes

The API defines custom exception classes for different error scenarios:

```python
class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass

class PermissionError(Exception):
    """Raised when a user lacks permission for an operation."""
    pass

class ResourceNotFoundError(Exception):
    """Raised when a requested resource is not found."""
    def __init__(self, resource_type, resource_id):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} with ID {resource_id} not found")

class ConflictError(Exception):
    """Raised when a request conflicts with the current state."""
    def __init__(self, message, details=None):
        self.details = details
        super().__init__(message)

class ProcessingError(Exception):
    """Raised when a valid request cannot be processed."""
    def __init__(self, message, reason):
        self.reason = reason
        super().__init__(message)

class RateLimitExceededError(Exception):
    """Raised when rate limits are exceeded."""
    def __init__(self, limit, retry_after):
        self.limit = limit
        self.retry_after = retry_after
        super().__init__("Rate limit exceeded")
```

## Client-Side Error Handling

The Phaser.js client should implement consistent error handling:

```javascript
// Example of client-side error handling
async function callApi(endpoint, method, data) {
  try {
    const response = await fetch(endpoint, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
      },
      body: method !== 'GET' ? JSON.stringify(data) : undefined
    });
    
    // Parse the response body
    const responseData = await response.json();
    
    // Check if the response indicates an error
    if (!response.ok) {
      // Handle specific error types
      switch (response.status) {
        case 401:
          // Redirect to login
          redirectToLogin();
          break;
        case 403:
          // Show permission error
          showErrorMessage("You don't have permission to perform this action");
          break;
        case 404:
          // Show not found error
          showErrorMessage(`The requested ${responseData.details?.resourceType || 'resource'} was not found`);
          break;
        case 429:
          // Handle rate limiting
          const retryAfter = responseData.details?.retryAfter || 60;
          showErrorMessage(`Too many requests. Please try again in ${retryAfter} seconds.`);
          break;
        default:
          // Show generic error message for other errors
          showErrorMessage(responseData.message || "An error occurred");
      }
      
      // Reject the promise with the error details
      return Promise.reject(responseData);
    }
    
    // Return successful response data
    return responseData;
  } catch (error) {
    // Handle network errors or parsing errors
    showErrorMessage("Network error or server unavailable");
    return Promise.reject(error);
  }
}
```

## Error Logging and Monitoring

All API errors are logged for monitoring and debugging:

1. **Validation errors** (400) are logged at the `INFO` level
2. **Authentication errors** (401) are logged at the `WARNING` level with user IP
3. **Permission errors** (403) are logged at the `WARNING` level with user ID and action
4. **Not found errors** (404) are logged at the `INFO` level
5. **Conflict errors** (409) are logged at the `INFO` level
6. **Processing errors** (422) are logged at the `WARNING` level
7. **Rate limit errors** (429) are logged at the `WARNING` level with user IP
8. **Server errors** (500) are logged at the `ERROR` level with full stack traces

Log entries include:
- Timestamp
- Error type
- User ID (when authenticated)
- Request endpoint and method
- Request parameters (sanitized of sensitive data)
- Error details
- Stack trace (for 500 errors)

## Error Prevention Strategies

The API implements several strategies to prevent common errors:

1. **Input Validation**: All request inputs are validated using Pydantic models
2. **Preconditions**: Operations check preconditions before processing (e.g., checking if an NPC exists)
3. **Transactions**: Database operations use transactions to maintain consistency
4. **Rate Limiting**: API endpoints have rate limits to prevent abuse
5. **Graceful Degradation**: The tiered AI system gracefully falls back to simpler processing when advanced tiers fail

## Debugging Support

For development and testing, the API provides additional debugging information when the `DEBUG` environment variable is set:

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred while processing the request",
  "details": null,
  "_debug": {
    "exception": "ValueError: Invalid parameter value",
    "location": "npc_service.py:127",
    "timestamp": "2025-03-12T10:23:45Z"
  }
}
```

The `_debug` field is only included in non-production environments.

## Conclusion

The Tokyo Train Station Adventure API's error handling system ensures:

1. **Consistency**: All errors follow a predictable structure
2. **Clarity**: Error messages are clear and actionable
3. **Security**: Error details don't expose sensitive information
4. **Testability**: Structured errors are easy to test against
5. **Client Support**: Clients can implement reliable error handling
6. **Monitoring**: All errors are properly logged for troubleshooting

By following these error handling conventions, the API provides a robust and reliable interface for the game client while making troubleshooting straightforward for developers.
