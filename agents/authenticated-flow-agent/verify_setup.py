#!/usr/bin/env python3
"""
Setup Verification Script

This script verifies that the authentication flow agent setup is correct
before attempting to run the full system.
"""

import os
import sys


def check_file_exists(file_path, description):
    """Check if a required file exists."""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (NOT FOUND)")
        return False


def check_python_import(module_name):
    """Check if a Python module can be imported."""
    try:
        __import__(module_name)
        print(f"✅ Python import: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ Python import: {module_name} ({e})")
        return False


def verify_setup():
    """Verify the complete setup."""
    print("🔍 Verifying Authentication Flow Agent Setup")
    print("=" * 50)

    all_good = True

    # Check directory structure
    print("\n📁 Directory Structure:")
    files_to_check = [
        ("src/agent.py", "Orchestrator agent"),
        ("src/tools/auth_verification_tool.py", "Auth verification tool"),
        ("auth-verification-remote/src/agent.py", "Remote agent"),
        ("auth-verification-remote/src/tools/auth_verification_tool.py", "Remote auth tool"),
        ("config/agent_config.yaml", "Agent configuration"),
        ("config/oauth_config.yaml", "OAuth configuration"),
        (".env", "Environment configuration"),
        ("requirements.txt", "Python dependencies"),
        ("start_agents.sh", "Startup script"),
        ("test_auth_flow.py", "Test suite"),
        ("quick_test.py", "Quick test"),
        ("README.md", "Documentation")
    ]

    for file_path, description in files_to_check:
        if not check_file_exists(file_path, description):
            all_good = False

    # Check executable permissions
    print("\n🔧 Executable Permissions:")
    if os.access("start_agents.sh", os.X_OK):
        print("✅ start_agents.sh is executable")
    else:
        print("❌ start_agents.sh is not executable")
        print("   Run: chmod +x start_agents.sh")
        all_good = False

    # Check Python dependencies
    print("\n🐍 Python Dependencies:")
    required_modules = [
        "google.adk.agents",
        "google.adk.tools",
        "starlette",
        "uvicorn",
        "httpx",
        "dotenv"
    ]

    for module in required_modules:
        if not check_python_import(module):
            all_good = False

    # Check ports availability
    print("\n🌐 Port Availability:")
    import socket

    def check_port(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                print(f"✅ Port {port} is available")
                return True
            except OSError:
                print(f"❌ Port {port} is in use")
                return False

    if not check_port(8001):
        all_good = False
    if not check_port(8002):
        all_good = False

    # Check environment variables
    print("\n🔐 Environment Configuration:")
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            env_content = f.read()

        required_vars = [
            "AGENT_NAME",
            "GOOGLE_OAUTH_CLIENT_ID",
            "GOOGLE_OAUTH_CLIENT_SECRET",
            "BEARER_TOKEN_VALIDATION"
        ]

        for var in required_vars:
            if var in env_content:
                print(f"✅ Environment variable: {var}")
            else:
                print(f"⚠️ Environment variable missing: {var}")

    # Summary
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 Setup verification completed successfully!")
        print("\n📋 Next steps:")
        print("1. Create virtual environment: python3 -m venv venv")
        print("2. Activate virtual environment: source venv/bin/activate")
        print("3. Install dependencies: pip install -r requirements.txt")
        print("4. Install remote dependencies: pip install -r auth-verification-remote/requirements.txt")
        print("5. Start agents: ./start_agents.sh")
        print("6. Run tests: python quick_test.py")
        return True
    else:
        print("❌ Setup verification found issues!")
        print("\n🔧 Please fix the issues above before proceeding.")
        return False


if __name__ == "__main__":
    success = verify_setup()
    sys.exit(0 if success else 1)