#!/bin/bash

# Test authentication forwarding to remote agent with bearer token
curl -X POST http://localhost:8001/ \
  -H "Authorization: Bearer test-token-123" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-1",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "auth-validation-test",
        "role": "user",
        "parts": [{
          "text": "Please delegate this task to the auth_validation_agent: validate my authentication context"
        }]
      }
    }
  }'