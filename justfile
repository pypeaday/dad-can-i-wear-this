# Get current version
get-version:
    hatch version
# Build Docker image with version tag
build:
    docker context use default
    just get-version | xargs -I {} docker build -t registry.paynepride.com/dad-can-i-wear:{} .
    docker tag registry.paynepride.com/dad-can-i-wear:$(just get-version) registry.paynepride.com/dad-can-i-wear:latest

# Push Docker image with version tag
build-and-push:
    docker context use default
    just build
    just get-version | xargs -I {} docker push registry.paynepride.com/dad-can-i-wear:{}
    docker push registry.paynepride.com/dad-can-i-wear:latest

# Ensure we're on main branch and up to date
check-main:
    #!/usr/bin/env bash
    set -euo pipefail
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "main" ]; then
        echo "Error: Must be on main branch"
        exit 1
    fi
    git fetch origin
    local_sha=$(git rev-parse HEAD)
    remote_sha=$(git rev-parse origin/main)
    if [ "$local_sha" != "$remote_sha" ]; then
        echo "Error: Local main is not up to date with origin"
        exit 1
    fi

# Create GitHub release with changelog
create-github-release:
    #!/usr/bin/env bash
    set -euo pipefail
    version=$(just get-version)
    # Extract changes since last tag
    last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [ -n "$last_tag" ]; then
        changelog=$(git log --pretty=format:"- %s" $last_tag..HEAD)
    else
        changelog=$(git log --pretty=format:"- %s")
    fi
    # Create GitHub release
    echo "$changelog" | gh release create v${version} \
        --title "Release v${version}" \
        --notes-file -

# Release a new version (bump version, create release, build/push Docker)
release type="patch":
    #!/usr/bin/env bash
    set -euo pipefail
    # Ensure were on main and up to date
    just check-main
    
    # Get current version before bump
    old_version=$(just get-version)
    
    # Use hatch to bump version
    hatch version {{type}}
    new_version=$(just get-version)
    
    # Commit version bump
    git add app/__about__.py
    git commit -m "chore: bump version to v${new_version}"
    
    # Create and push git tag
    git tag -a "v${new_version}" -m "Release v${new_version}"
    git push origin main "v${new_version}"
    
    # Create GitHub release
    just create-github-release
    
    # Build and push Docker image
    just build-and-push
    
    echo "Released v${new_version}"
    echo "Previous version was v${old_version}"

up:
    docker context use default
    docker compose up --build