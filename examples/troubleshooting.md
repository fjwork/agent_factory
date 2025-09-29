# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the agent-template, remote agents, and authentication forwarding.

## 🚨 Quick Diagnostics

### System Health Check

Run this quick diagnostic script to check your setup:

```bash
#!/bin/bash
echo "🔍 Agent Template Diagnostics"
echo "================================"

# Check Python version
echo "Python version:"
python --version

# Check dependencies
echo -e "\n📦 Checking dependencies:"
python -c "import google.adk; print('✅ Google ADK installed')" 2>/dev/null || echo "❌ Google ADK not installed"
python -c "import yaml; print('✅ PyYAML installed')" 2>/dev/null || echo "❌ PyYAML not installed"
python -c "import httpx; print('✅ HTTPX installed')" 2>/dev/null || echo "❌ HTTPX not installed"

# Check configuration files
echo -e "\n📁 Checking configuration files:"
[ -f "config/agent_config.yaml" ] && echo "✅ agent_config.yaml exists" || echo "❌ agent_config.yaml missing"
[ -f "config/remote_agents.yaml" ] && echo "✅ remote_agents.yaml exists" || echo "ℹ️  remote_agents.yaml not found (standalone mode)"

# Check ports
echo -e "\n🔌 Checking port availability:"
for port in 8001 8002 8003 8004; do
  if lsof -i :$port >/dev/null 2>&1; then
    echo "⚠️  Port $port is in use"
  else
    echo "✅ Port $port is available"
  fi
done

# Check environment variables
echo -e "\n🌍 Environment variables:"
echo "MODEL_NAME: ${MODEL_NAME:-not set}"
echo "AGENT_NAME: ${AGENT_NAME:-not set}"
echo "LOG_LEVEL: ${LOG_LEVEL:-not set}"

echo -e "\n🏁 Diagnostics complete"
```

Save as `diagnostics.sh`, make executable with `chmod +x diagnostics.sh`, and run with `./diagnostics.sh`.

## 🔧 Common Issues and Solutions

### 1. Agent Won't Start

#### Issue: "ModuleNotFoundError: No module named 'google.adk'"

**Cause**: Google ADK not installed or not in Python path.

**Solution**:
```bash
# Install Google ADK
pip install google-adk

# Verify installation
python -c "import google.adk; print('ADK installed successfully')"

# If still failing, check Python environment
which python
pip list | grep adk
```

#### Issue: "Port already in use" error

**Cause**: Another process is using the required port.

**Solution**:
```bash
# Find what's using the port
lsof -i :8001

# Kill the process (replace PID with actual process ID)
kill -9 <PID>

# Or use a different port
export AGENT_PORT="8101"
python src/agent.py
```

#### Issue: "Permission denied" when binding to port

**Cause**: Insufficient permissions to bind to the port.

**Solution**:
```bash
# Use a port > 1024 (non-privileged)
export AGENT_PORT="8001"

# Or run with sudo (not recommended for development)
sudo python src/agent.py

# Better: Use port forwarding if you need port 80/443
# iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8001
```

### 2. Remote Agents Not Loading

#### Issue: Agent runs in standalone mode when remote agents expected

**Cause**: Remote agents configuration not found or invalid.

**Diagnostics**:
```bash
# Check if config file exists
ls -la config/remote_agents.yaml

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/remote_agents.yaml'))"

# Check content
cat config/remote_agents.yaml
```

**Solution**:
```bash
# Copy a working configuration
cp examples/configurations/complete_remote_agents.yaml config/remote_agents.yaml

# Or create minimal config
cat > config/remote_agents.yaml << EOF
remote_agents:
  - name: "data_analysis_agent"
    description: "Data analysis agent"
    agent_card_url: "http://localhost:8002/a2a/data_analysis_agent"
    enabled: true
EOF
```

#### Issue: "Failed to connect to remote agent"

**Cause**: Remote agent not running or not accessible.

**Diagnostics**:
```bash
# Check if remote agent is running
curl http://localhost:8002/health

# Check agent card endpoint
curl http://localhost:8002/.well-known/agent-card.json

# Check if port is open
nc -zv localhost 8002
```

**Solution**:
```bash
# Start the remote agent
python testing/remote_agents/data_analysis_agent/src/agent.py

# Or start in background
nohup python testing/remote_agents/data_analysis_agent/src/agent.py &

# Verify it's running
curl http://localhost:8002/health
```

### 3. Authentication Issues

#### Issue: "Authentication failed" or bearer token not working

**Cause**: OAuth configuration incorrect or bearer token malformed.

**Diagnostics**:
```bash
# Check OAuth environment variables
echo "Client ID: $OAUTH_CLIENT_ID"
echo "Client Secret: $OAUTH_CLIENT_SECRET"

# Test bearer token format
echo "Bearer token: $TEST_BEARER_TOKEN"

# Check authentication endpoints
curl http://localhost:8001/auth/status
```

**Solution**:
```bash
# Set test OAuth credentials
export OAUTH_CLIENT_ID="test-client-id"
export OAUTH_CLIENT_SECRET="test-client-secret"

# Create a test bearer token
python -c "
from testing.utils.auth_test_utils import BearerTokenGenerator
gen = BearerTokenGenerator()
token = gen.create_test_token('test@example.com')
print(f'Test token: {token}')
"

# Test authentication
curl -X POST http://localhost:8001/a2a \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"test","method":"message/send","params":{"message":{"messageId":"test","role":"user","parts":[{"text":"test"}]}}}'
```

#### Issue: Authentication not forwarded to remote agents

**Cause**: Session state not preserved or A2A protocol issue.

**Diagnostics**:
```bash
# Test authentication forwarding
python testing/test_auth_forwarding.py

# Check logs for authentication context
export LOG_LEVEL="DEBUG"
python src/agent.py
```

**Solution**:
```bash
# Verify remote agents are properly implementing auth context extraction
# Check the _extract_auth_info method in remote agent tools

# Test with explicit auth verification
curl -X POST http://localhost:8001/a2a \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "auth-test",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "auth-test",
        "role": "user",
        "parts": [{"text": "Please delegate to data analysis agent and verify auth forwarding"}]
      }
    }
  }'
```

### 4. Performance Issues

#### Issue: Slow response times or timeouts

**Cause**: Network latency, resource constraints, or inefficient processing.

**Diagnostics**:
```bash
# Check response times
time curl http://localhost:8001/health

# Monitor resource usage
top -p $(pgrep -f agent.py)

# Check network connectivity
ping localhost
traceroute localhost
```

**Solution**:
```bash
# Increase timeout values
export REQUEST_TIMEOUT="60"
export CONNECTION_TIMEOUT="30"

# Optimize logging level
export LOG_LEVEL="WARN"

# Use production model settings
export MODEL_NAME="gemini-2.0-flash"

# Consider load balancing for high traffic
# See multi-agent setup guide for load balancing configuration
```

#### Issue: High memory usage

**Cause**: Memory leaks or inefficient model loading.

**Diagnostics**:
```bash
# Monitor memory usage
ps aux | grep agent.py

# Check for memory leaks
valgrind --tool=memcheck python src/agent.py

# Profile memory usage
python -m memory_profiler src/agent.py
```

**Solution**:
```bash
# Limit worker processes
export MAX_WORKERS="2"

# Use memory-efficient settings
export BATCH_SIZE="1"
export MAX_CONTEXT_LENGTH="4096"

# Restart agents periodically in production
# Add to crontab: 0 2 * * * /path/to/restart_agents.sh
```

### 5. Network and Connectivity Issues

#### Issue: "Connection refused" when connecting to remote agents

**Cause**: Network configuration, firewall, or agent not listening on expected interface.

**Diagnostics**:
```bash
# Check which interface agent is binding to
netstat -tlnp | grep 8002

# Check firewall rules
iptables -L

# Test local connectivity
curl -v http://localhost:8002/health

# Test from another machine
curl -v http://your-server-ip:8002/health
```

**Solution**:
```bash
# Ensure agent binds to all interfaces
export DATA_ANALYSIS_HOST="0.0.0.0"

# Allow traffic through firewall
sudo ufw allow 8002

# For Docker, ensure ports are properly exposed
docker run -p 8002:8002 your-agent-image

# For cloud deployments, check security groups/firewall rules
```

#### Issue: SSL/TLS certificate errors in production

**Cause**: Invalid or expired certificates.

**Diagnostics**:
```bash
# Check certificate validity
openssl x509 -in /path/to/cert.pem -text -noout

# Test SSL connection
openssl s_client -connect your-domain.com:443

# Check certificate chain
curl -vI https://your-domain.com
```

**Solution**:
```bash
# Renew certificates (Let's Encrypt example)
certbot renew

# Update agent configuration with new certificate paths
export SSL_CERT_PATH="/etc/letsencrypt/live/your-domain.com/fullchain.pem"
export SSL_KEY_PATH="/etc/letsencrypt/live/your-domain.com/privkey.pem"

# Restart agents after certificate update
systemctl restart agent-service
```

### 6. Configuration Issues

#### Issue: YAML parsing errors

**Cause**: Invalid YAML syntax in configuration files.

**Diagnostics**:
```bash
# Validate YAML syntax
python -c "import yaml; print(yaml.safe_load(open('config/remote_agents.yaml')))"

# Check for common YAML issues
cat -A config/remote_agents.yaml  # Shows tabs/spaces
```

**Solution**:
```bash
# Use proper YAML formatting
# Ensure consistent indentation (spaces, not tabs)
# Ensure proper quoting of strings with special characters

# Example of correct format:
cat > config/remote_agents.yaml << 'EOF'
remote_agents:
  - name: "data_analysis_agent"
    description: "Data analysis service"
    agent_card_url: "http://localhost:8002/a2a/data_analysis_agent"
    enabled: true
EOF

# Validate after editing
python -c "import yaml; yaml.safe_load(open('config/remote_agents.yaml'))"
```

#### Issue: Environment variables not being read

**Cause**: Environment not properly set or shell configuration issues.

**Diagnostics**:
```bash
# Check if variables are set
env | grep AGENT
printenv | grep OAUTH

# Check shell configuration
echo $SHELL
source ~/.bashrc  # or ~/.zshrc
```

**Solution**:
```bash
# Set variables in current session
export AGENT_NAME="MyAgent"
export OAUTH_CLIENT_ID="your-client-id"

# Add to shell profile for persistence
echo 'export AGENT_NAME="MyAgent"' >> ~/.bashrc
source ~/.bashrc

# Use .env file for project-specific variables
cat > .env << EOF
AGENT_NAME=MyAgent
OAUTH_CLIENT_ID=your-client-id
EOF

# Load .env file
set -a; source .env; set +a
```

## 🐛 Debug Mode

### Enable Comprehensive Debugging

```bash
# Set debug environment
export LOG_LEVEL="DEBUG"
export DEBUG_MODE="true"
export TRACE_REQUESTS="true"

# Start agent with debug output
python src/agent.py 2>&1 | tee debug.log

# Or use Python debugger
python -m pdb src/agent.py
```

### Debug Remote Agent Communication

```bash
# Enable A2A debug logging
export A2A_DEBUG="true"
export LOG_A2A_REQUESTS="true"

# Monitor network traffic
sudo tcpdump -i lo port 8002

# Use verbose curl for API testing
curl -v -X POST http://localhost:8001/a2a \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"debug","method":"message/send","params":{"message":{"messageId":"debug","role":"user","parts":[{"text":"debug test"}]}}}'
```

### Application-Specific Debugging

```python
# Add debug prints to agent code
import logging
logging.basicConfig(level=logging.DEBUG)

# In your agent tools:
def execute_with_context(self, tool_context, **kwargs):
    logger.debug(f"Tool context: {tool_context}")
    logger.debug(f"Session state: {tool_context.state}")
    logger.debug(f"Kwargs: {kwargs}")

    # Your tool logic here

    logger.debug(f"Result: {result}")
    return result
```

## 📊 Monitoring and Logging

### Log Analysis

```bash
# Real-time log monitoring
tail -f debug.log | grep ERROR

# Search for specific issues
grep -i "authentication" debug.log
grep -i "connection" debug.log
grep -i "timeout" debug.log

# Log rotation for production
logrotate -f /etc/logrotate.d/agent-template
```

### Health Monitoring

```bash
# Create a health check script
cat > health_check.sh << 'EOF'
#!/bin/bash
AGENTS=("8001" "8002" "8003" "8004")

for port in "${AGENTS[@]}"; do
  if curl -f -s http://localhost:$port/health > /dev/null; then
    echo "✅ Agent on port $port is healthy"
  else
    echo "❌ Agent on port $port is unhealthy"
  fi
done
EOF

chmod +x health_check.sh
./health_check.sh
```

### Performance Monitoring

```bash
# Monitor response times
while true; do
  time curl -s http://localhost:8001/health > /dev/null
  sleep 5
done

# Monitor resource usage
watch -n 5 'ps aux | grep agent.py'

# Network monitoring
watch -n 5 'netstat -an | grep 800[1-4]'
```

## 🚨 Emergency Procedures

### Service Recovery

```bash
# Kill all agent processes
pkill -f agent.py

# Restart all services
./start_all_agents.sh

# Or restart individual agents
python src/agent.py &
python testing/remote_agents/data_analysis_agent/src/agent.py &
python testing/remote_agents/notification_agent/src/agent.py &
python testing/remote_agents/approval_agent/src/agent.py &
```

### Rollback Configuration

```bash
# Backup current config
cp config/remote_agents.yaml config/remote_agents.yaml.backup

# Restore known working config
cp examples/configurations/complete_remote_agents.yaml config/remote_agents.yaml

# Restart services
pkill -f agent.py
./start_all_agents.sh
```

### Data Recovery

```bash
# Check for backup files
ls -la config/*.backup
ls -la logs/

# Restore from backup
cp config/agent_config.yaml.backup config/agent_config.yaml

# Verify configuration
python -c "import yaml; print(yaml.safe_load(open('config/agent_config.yaml')))"
```

## 📞 Getting Help

### Community Support

1. **GitHub Issues**: Report bugs and request features
2. **Documentation**: Check official ADK and agent-template docs
3. **Stack Overflow**: Search for related questions with tags `google-adk`, `agent-to-agent`

### Diagnostic Information to Include

When reporting issues, include:

```bash
# System information
uname -a
python --version
pip list | grep -E "(google|adk|yaml|httpx)"

# Configuration files (remove sensitive data)
cat config/agent_config.yaml
cat config/remote_agents.yaml

# Environment variables (remove sensitive data)
env | grep -E "(AGENT|OAUTH|MODEL)" | sed 's/=.*$/=***/'

# Error logs
tail -50 debug.log

# Network configuration
netstat -tlnp | grep 800[1-4]
```

### Self-Help Checklist

Before seeking help, try:

- [ ] Run the diagnostic script
- [ ] Check all configuration files
- [ ] Verify all required ports are available
- [ ] Test with minimal configuration
- [ ] Review recent changes
- [ ] Check logs for error messages
- [ ] Try restarting all services
- [ ] Test with debug logging enabled

## 🔗 Related Documentation

- [Standalone Setup Guide](standalone_setup.md)
- [Multi-Agent Setup Guide](multi_agent_setup.md)
- [Testing Documentation](../testing/README.md)
- [Configuration Examples](configurations/)
- [Authentication Guide](authentication_guide.md)