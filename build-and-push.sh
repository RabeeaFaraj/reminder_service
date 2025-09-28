#!/bin/bash

# Build and Push Script for Reminder Service
# This script automatically increments version and pushes to Docker Hub

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_HUB_USER="rabeeafaraj"
IMAGE_NAME="reminder-service"
VERSION_FILE="VERSION"

# Functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if VERSION file exists
if [ ! -f "$VERSION_FILE" ]; then
    print_error "VERSION file not found. Creating initial version 0.0.1"
    echo "0.0.1" > $VERSION_FILE
fi

# Read current version
CURRENT_VERSION=$(cat $VERSION_FILE)
print_status "Current version: $CURRENT_VERSION"

# Parse version components
IFS='.' read -r -a version_parts <<< "$CURRENT_VERSION"
major="${version_parts[0]}"
minor="${version_parts[1]}"
patch="${version_parts[2]}"

# Increment patch version
patch=$((patch + 1))
NEW_VERSION="$major.$minor.$patch"

print_status "New version will be: $NEW_VERSION"

# Ask for confirmation
read -p "Do you want to build and push version $NEW_VERSION? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Build cancelled by user"
    exit 0
fi

# Update VERSION file
echo "$NEW_VERSION" > $VERSION_FILE
print_success "Updated VERSION file to $NEW_VERSION"

# Build the Docker image
print_status "Building Docker image..."
docker build -t $DOCKER_HUB_USER/$IMAGE_NAME:$NEW_VERSION .
docker tag $DOCKER_HUB_USER/$IMAGE_NAME:$NEW_VERSION $DOCKER_HUB_USER/$IMAGE_NAME:latest

print_success "Docker image built successfully"

# Login to Docker Hub (if not already logged in)
print_status "Logging into Docker Hub..."
if ! docker info | grep -q "Username: $DOCKER_HUB_USER"; then
    docker login
fi

# Push to Docker Hub
print_status "Pushing image to Docker Hub..."
docker push $DOCKER_HUB_USER/$IMAGE_NAME:$NEW_VERSION
docker push $DOCKER_HUB_USER/$IMAGE_NAME:latest

print_success "Image pushed successfully!"

# Update .env file with new version
if [ -f ".env" ]; then
    if grep -q "REMINDER_SERVICE_VERSION" .env; then
        sed -i "s/REMINDER_SERVICE_VERSION=.*/REMINDER_SERVICE_VERSION=$NEW_VERSION/" .env
    else
        echo "REMINDER_SERVICE_VERSION=$NEW_VERSION" >> .env
    fi
    print_success "Updated .env file with new version"
fi

# Show final status
print_success "Build and push completed!"
echo
echo "📦 Image Details:"
echo "   Repository: $DOCKER_HUB_USER/$IMAGE_NAME"
echo "   Version: $NEW_VERSION"
echo "   Tags: $NEW_VERSION, latest"
echo
echo "🚀 To deploy with docker-compose:"
echo "   docker-compose pull"
echo "   docker-compose up -d"
echo
echo "🔗 Docker Hub URL:"
echo "   https://hub.docker.com/r/$DOCKER_HUB_USER/$IMAGE_NAME"