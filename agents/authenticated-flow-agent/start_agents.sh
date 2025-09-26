#!/bin/bash

# Start Authentication Flow Verification Agents
# This script starts both the remote agent and orchestrator agent in separate processes

echo "🚀 Starting Authentication Flow Verification Agents"
echo "=================================================="

# Function to check if port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $1 is already in use. Please stop the process using this port."
        return 1
    fi
    return 0
}

# Check if required ports are available
echo "🔍 Checking port availability..."
check_port 8001 || exit 1
check_port 8002 || exit 1
echo "✅ Ports 8001 and 8002 are available"

# Navigate to the agents directory
cd "$(dirname "$0")"

# Start remote agent in background
echo "🔧 Starting Auth Verification Remote Agent (port 8002)..."
cd auth-verification-remote/src
python agent.py &
REMOTE_PID=$!
echo "✅ Remote agent started with PID: $REMOTE_PID"

# Wait a moment for remote agent to start
sleep 3

# Start orchestrator agent in background
echo "🔧 Starting Authenticated Flow Agent (port 8001)..."
cd ../../src
python agent.py &
ORCHESTRATOR_PID=$!
echo "✅ Orchestrator agent started with PID: $ORCHESTRATOR_PID"

# Wait for agents to initialize
sleep 5

echo ""
echo "🎉 Both agents are starting up!"
echo "=================================================="
echo "📋 Remote Agent:      http://localhost:8002"
echo "📋 Orchestrator:      http://localhost:8001"
echo "🔍 Health Checks:"
echo "   - Remote:          curl http://localhost:8002/health"
echo "   - Orchestrator:    curl http://localhost:8001/health"
echo "🔐 Auth Status:"
echo "   - Remote:          curl http://localhost:8002/auth/dual-status"
echo "   - Orchestrator:    curl http://localhost:8001/auth/dual-status"
echo ""
echo "📝 To run tests:"
echo "   python test_auth_flow.py"
echo ""
echo "🛑 To stop agents:"
echo "   kill $REMOTE_PID $ORCHESTRATOR_PID"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping agents..."
    kill $REMOTE_PID $ORCHESTRATOR_PID 2>/dev/null
    echo "✅ Agents stopped"
    exit 0
}

# Trap CTRL+C
trap cleanup SIGINT SIGTERM

echo "💡 Press Ctrl+C to stop both agents"
echo "📊 Monitoring agent processes..."

# Monitor processes
while kill -0 $REMOTE_PID 2>/dev/null && kill -0 $ORCHESTRATOR_PID 2>/dev/null; do
    sleep 1
done

echo "❌ One or both agents have stopped"
cleanup