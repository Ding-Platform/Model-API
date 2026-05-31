#!/bin/bash

# Model-API Production Deployment Script
set -e

echo "====================================="
echo "Model-API Production Deployment"
echo "====================================="
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
MODEL_API_HEALTH_URL="${MODEL_API_HEALTH_URL:-http://127.0.0.1:8000/api/v1/health}"

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_success "Docker is installed ($(docker --version))"
}

check_docker_compose() {
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    print_success "Docker Compose is installed ($(docker compose version))"
}

check_env_file() {
    if [ ! -f .env ]; then
        print_error "Missing .env in $PROJECT_ROOT — copy from .env.example and configure secrets."
        exit 1
    fi
    print_success ".env file present"
}

stop_stale_containers() {
    print_info "Removing stale Model-API containers (if any)..."
    docker compose $COMPOSE_FILES down --remove-orphans 2>/dev/null || true
    print_success "Compose stack reset"
}

deploy_services() {
    print_info "Building and starting Model-API services..."
    print_info "This may take several minutes on first run..."

    docker compose $COMPOSE_FILES up -d --build --force-recreate

    print_success "Services built and started"
}

wait_for_health() {
    print_info "Waiting for Model-API health at $MODEL_API_HEALTH_URL ..."

    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "$MODEL_API_HEALTH_URL" > /dev/null 2>&1; then
            print_success "Model-API is healthy"
            return 0
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done

    echo ""
    print_error "Model-API failed health check ($MODEL_API_HEALTH_URL)"
    print_info "Check logs: docker compose $COMPOSE_FILES logs --tail=80 ai-server-api"
    return 1
}

display_summary() {
    SERVER_IP=$(curl -s ipv4.icanhazip.com 2>/dev/null || curl -s -4 ifconfig.me 2>/dev/null || echo "localhost")

    echo ""
    echo "====================================="
    echo "Model-API Deployment Summary"
    echo "====================================="
    echo ""
    print_success "Model-API has been deployed successfully!"
    echo ""
    echo "Access:"
    echo "  Direct (loopback):     http://127.0.0.1:8000/api/v1"
    echo "  Via Nginx (public):    http://$SERVER_IP/model-api/"
    echo "  Health:                http://127.0.0.1:8000/api/v1/health"
    echo ""
    echo "Useful commands:"
    echo "  View logs:    docker compose $COMPOSE_FILES logs -f ai-server-api"
    echo "  Stop:         docker compose $COMPOSE_FILES down"
    echo "  Restart API:  docker compose $COMPOSE_FILES restart ai-server-api"
    echo "  Status:       docker compose $COMPOSE_FILES ps"
    echo ""
    print_info "Reload host Nginx after updating nginx/ding.conf:"
    echo "  sudo nginx -t && sudo systemctl reload nginx"
    echo ""
}

main() {
    echo ""
    check_docker
    check_docker_compose
    check_env_file
    echo ""

    stop_stale_containers
    echo ""

    deploy_services
    echo ""

    wait_for_health
    echo ""

    display_summary
}

main
