#!/bin/bash

# Test multi-agent communication with bearer token
curl -X POST http://localhost:8001/ \
  -H "Authorization: Bearer test-token-123" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-1",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "multi-agent-test",
        "role": "user",
        "parts": [{
          "text": "Please delegate this task: analyze my sales data using the data_analysis_agent, return the result"
        }]
      }
    }
  }'