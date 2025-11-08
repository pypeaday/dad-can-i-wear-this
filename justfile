# Default registry if not set in environment
REGISTRY := "docker.io/username"

# Get current version
get-version:
    hatch version

# # Build Docker image with version tag
# build:
#     docker context use default
#     just get-version | xargs -I {} docker build -t ${REGISTRY}/dad-can-i-wear:{} .
#     docker tag ${REGISTRY}/dad-can-i-wear:$(just get-version) ${REGISTRY}/dad-can-i-wear:latest
#
# # Push Docker image with version tag
# build-and-push:
#     docker context use default
#     just build
#     just get-version | xargs -I {} docker push ${REGISTRY}/dad-can-i-wear:{}
#     docker push ${REGISTRY}/dad-can-i-wear:latest

# Release a new version (bump version, create release, build/push Docker)
release type="patch":
    #!/usr/bin/env bash
    set -euo pipefail
    # Get current version before bump
    old_version=$(hatch version)
    
    # Use hatch to bump version
    hatch version {{ type }}
    new_version=$(hatch version)
    
    # Commit version bump
    git add app/__about__.py
    git commit -m "chore: bump version to v${new_version}"
    
    # Create and push git tag
    git tag -a "v${new_version}" -m "Release v${new_version}"
    git push origin main "v${new_version}" || echo "no remote"
    
    # Build and push Docker image
    just build-and-push
    
    echo "Released v${new_version}"
    echo "Previous version was v${old_version}"

up:
    docker context use default
    docker compose up --build
