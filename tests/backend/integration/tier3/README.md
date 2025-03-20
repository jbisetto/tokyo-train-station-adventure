# Tier 3 Integration Tests

This directory contains integration tests for the Tier 3 processor, which uses AWS Bedrock for cloud-based LLM processing.

## Test Files

- `test_bedrock.py` - Tests for the AWS Bedrock integration

## Requirements

To run these tests, you need:

1. AWS credentials configured (via environment variables or `~/.aws/credentials`)
2. Access to AWS Bedrock models
3. Environment variables set:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION` (e.g., `us-east-1`)

## Running Tests

You can run the tests using pytest:

```bash
# From the project root
python -m pytest tests/backend/integration/tier3 -v

# Or from the tests directory
python -m pytest backend/integration/tier3 -v
```

## Quota and Cost Considerations

Please note that running these tests will make actual API calls to AWS Bedrock, which:

1. Counts against your AWS Bedrock quotas
2. Incurs costs according to your AWS Bedrock pricing

Consider using mock objects for frequent development testing and only use real API calls for final verification. 