#!/bin/bash

# ADK Agent Template Setup Script
# This script sets up the environment for deploying ADK agents

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Python
    if ! command_exists python3; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    log_success "Python 3 found: $(python3 --version)"

    # Check pip
    if ! command_exists pip3; then
        log_error "pip3 is required but not installed"
        exit 1
    fi
    log_success "pip3 found"

    # Check gcloud
    if ! command_exists gcloud; then
        log_error "Google Cloud CLI is required but not installed"
        log_info "Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    log_success "Google Cloud CLI found: $(gcloud version --format='value(Google Cloud SDK)' 2>/dev/null)"

    # Check Docker (optional for local development)
    if command_exists docker; then
        log_success "Docker found: $(docker --version)"
    else
        log_warning "Docker not found (optional for local development)"
    fi
}

# Authenticate with Google Cloud
authenticate_gcloud() {
    log_info "Checking Google Cloud authentication..."

    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "."; then
        log_info "Authenticating with Google Cloud..."
        gcloud auth login
        gcloud auth application-default login
    else
        log_success "Already authenticated with Google Cloud"
    fi
}

# Set up project
setup_project() {
    # Get project ID
    if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
        read -p "Enter your Google Cloud Project ID: " GOOGLE_CLOUD_PROJECT
    fi

    if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
        log_error "Project ID is required"
        exit 1
    fi

    log_info "Setting up project: $GOOGLE_CLOUD_PROJECT"
    gcloud config set project "$GOOGLE_CLOUD_PROJECT"

    # Get location
    if [ -z "$GOOGLE_CLOUD_LOCATION" ]; then
        GOOGLE_CLOUD_LOCATION="us-central1"
        log_info "Using default location: $GOOGLE_CLOUD_LOCATION"
    fi

    # Export environment variables
    export GOOGLE_CLOUD_PROJECT
    export GOOGLE_CLOUD_LOCATION

    log_success "Project configured: $GOOGLE_CLOUD_PROJECT in $GOOGLE_CLOUD_LOCATION"
}

# Enable required APIs
enable_apis() {
    log_info "Enabling required Google Cloud APIs..."

    local apis=(
        "aiplatform.googleapis.com"
        "run.googleapis.com"
        "artifactregistry.googleapis.com"
        "secretmanager.googleapis.com"
        "cloudbuild.googleapis.com"
    )

    for api in "${apis[@]}"; do
        log_info "Enabling $api..."
        gcloud services enable "$api"
    done

    log_success "All required APIs enabled"
}

# Set up OAuth configuration
setup_oauth() {
    log_info "Setting up OAuth configuration..."

    # Check if OAuth client exists
    if [ -z "$GOOGLE_OAUTH_CLIENT_ID" ] || [ -z "$GOOGLE_OAUTH_CLIENT_SECRET" ]; then
        log_warning "OAuth credentials not found in environment variables"
        log_info "You'll need to:"
        log_info "1. Go to Google Cloud Console > APIs & Services > Credentials"
        log_info "2. Create an OAuth 2.0 Client ID for a Desktop application"
        log_info "3. Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET environment variables"
        log_info "4. Or store them in Google Secret Manager"

        read -p "Do you want to create secrets in Secret Manager now? (y/N): " create_secrets
        if [[ $create_secrets =~ ^[Yy]$ ]]; then
            create_oauth_secrets
        fi
    else
        log_success "OAuth credentials found in environment"
    fi
}

# Create OAuth secrets in Secret Manager
create_oauth_secrets() {
    log_info "Creating OAuth secrets in Secret Manager..."

    # Create secrets
    local secrets=(
        "oauth-client-id"
        "oauth-client-secret"
    )

    for secret in "${secrets[@]}"; do
        if ! gcloud secrets describe "$secret" >/dev/null 2>&1; then
            log_info "Creating secret: $secret"
            gcloud secrets create "$secret" --replication-policy="automatic"
        else
            log_info "Secret already exists: $secret"
        fi
    done

    log_info "Please add your OAuth credentials to the secrets:"
    log_info "gcloud secrets versions add oauth-client-id --data-file=-"
    log_info "gcloud secrets versions add oauth-client-secret --data-file=-"
}

# Install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."

    # Check if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
        log_success "Python dependencies installed"
    else
        log_warning "requirements.txt not found, skipping Python dependencies"
    fi

    # Install development dependencies if requested
    if [ -f "requirements-dev.txt" ] && [ "$1" = "dev" ]; then
        pip3 install -r requirements-dev.txt
        log_success "Development dependencies installed"
    fi
}

# Create environment file
create_env_file() {
    log_info "Creating environment configuration..."

    local env_file=".env"

    if [ ! -f "$env_file" ]; then
        cat > "$env_file" << EOF
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT
GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION

# Environment
ENVIRONMENT=development

# Agent Configuration
AGENT_NAME=MyAgent
AGENT_VERSION=1.0.0
MODEL_PROVIDER=gemini
MODEL_NAME=gemini-2.0-flash

# OAuth Configuration
OAUTH_DEFAULT_PROVIDER=google
OAUTH_FLOW_TYPE=device_flow
OAUTH_SCOPES=openid profile email
TOKEN_STORAGE_TYPE=secret_manager

# Security
OAUTH_REQUIRE_HTTPS=false

# A2A Configuration
A2A_HOST=0.0.0.0
A2A_PORT=8000
A2A_TRANSPORT=jsonrpc

# Cloud Run Configuration
CLOUD_RUN_SERVICE_NAME=\${AGENT_NAME}
CLOUD_RUN_ALLOW_UNAUTH=true

# Logging
LOG_LEVEL=INFO
EOF

        log_success "Environment file created: $env_file"
        log_info "Please review and customize the configuration in $env_file"
    else
        log_info "Environment file already exists: $env_file"
    fi
}

# Validate configuration
validate_config() {
    log_info "Validating configuration..."

    local config_files=(
        "config/agent_config.yaml"
        "config/oauth_config.yaml"
        "config/deployment_config.yaml"
    )

    for config_file in "${config_files[@]}"; do
        if [ -f "$config_file" ]; then
            log_success "Found: $config_file"
        else
            log_error "Missing: $config_file"
            exit 1
        fi
    done

    log_success "Configuration validation passed"
}

# Main setup function
main() {
    log_info "Starting ADK Agent Template Setup..."

    # Parse command line arguments
    local install_dev=false
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dev)
                install_dev=true
                shift
                ;;
            --project)
                GOOGLE_CLOUD_PROJECT="$2"
                shift 2
                ;;
            --location)
                GOOGLE_CLOUD_LOCATION="$2"
                shift 2
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --dev                Install development dependencies"
                echo "  --project PROJECT    Set Google Cloud project ID"
                echo "  --location LOCATION  Set Google Cloud location"
                echo "  -h, --help          Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Run setup steps
    check_prerequisites
    authenticate_gcloud
    setup_project
    enable_apis
    setup_oauth

    if [ "$install_dev" = true ]; then
        install_dependencies "dev"
    else
        install_dependencies
    fi

    create_env_file
    validate_config

    log_success "Setup completed successfully!"
    log_info ""
    log_info "Next steps:"
    log_info "1. Review and customize configuration files in the config/ directory"
    log_info "2. Set up your OAuth credentials in Google Cloud Console"
    log_info "3. Update the .env file with your specific settings"
    log_info "4. Deploy to Cloud Run: python deployment/cloud_run/deploy.py"
    log_info "5. Or deploy to Agent Engine: python deployment/agent_engine/deploy.py --action create"
}

# Run main function if script is executed directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi