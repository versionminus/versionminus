#!/usr/bin/env bash
# Enforce strict bash modes for safer execution
set -euo pipefail
# Explain: exit on any error, undefined variable usage, and fail the pipeline early

# Resolve repository root based on this script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Explain: get absolute path of the directory containing this script
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# Explain: navigate two levels up from script directory to the repo root

# Helper: echo a step title
step() { echo "==> $1"; }
# Explain: provide readable markers for each cleanup phase

# Bring down any Compose stacks in known compose files within the repo
step "Bringing down Compose stacks (with volumes & orphans)"
# Explain: announce the first cleanup phase for compose projects
while IFS= read -r compose_file; do
# Explain: iterate over each discovered compose file path
  ( cd "$(dirname "$compose_file")" && docker compose -f "$(basename "$compose_file")" down -v --remove-orphans 2>/dev/null || true )
# Explain: run docker compose down with volumes and orphan removal in that compose file's directory, ignore failures
done < <(find "$REPO_ROOT" -type f \( -name 'compose.yml' -o -name 'compose.yaml' -o -name 'docker-compose.yml' -o -name 'docker-compose.yaml' \))
# Explain: search the repository for common compose file names and feed them to the loop

# Stop all running containers
step "Stopping all running containers"
# Explain: announce container stop phase
docker ps -q | xargs -r docker stop
# Explain: stop containers only if any IDs are present

# Remove all containers (running or stopped)
step "Removing all containers"
# Explain: announce container removal phase
docker ps -aq | xargs -r docker rm -f
# Explain: force-remove containers only if any IDs are present

# Remove user-created networks while preserving Docker defaults
step "Removing user-created networks"
# Explain: announce network removal phase
docker network ls -q | xargs -r -I{} sh -c 'n=$(docker network inspect -f "{{.Name}}" {}); case "$n" in bridge|host|none) ;; *) docker network rm -f "$n" >/dev/null 2>&1 || true ;; esac'
# Explain: iterate over networks and delete all except the default bridge, host, and none networks
docker network prune -f >/dev/null 2>&1 || true
# Explain: prune dangling/unused networks as a safety sweep, ignore errors

# Remove all volumes (destructive for stored data)
step "Removing all volumes (destructive)"
# Explain: announce volume removal phase with data loss warning
docker volume ls -q | xargs -r docker volume rm -f
# Explain: remove all volumes only if any IDs are present
docker volume prune -f >/dev/null 2>&1 || true
# Explain: prune dangling/unused volumes, ignore errors

# Discover image references defined in this repository (compose files and Dockerfiles)
step "Discovering images defined in the repository"
# Explain: announce discovery phase for images to remove
mapfile -t COMPOSE_FILES < <(find "$REPO_ROOT" -type f \( -name 'compose.yml' -o -name 'compose.yaml' -o -name 'docker-compose.yml' -o -name 'docker-compose.yaml' \))
# Explain: collect all compose files into an array
mapfile -t DOCKERFILES < <(find "$REPO_ROOT" -type f \( -name 'Dockerfile' -o -name 'Dockerfile.*' \))
# Explain: collect all Dockerfiles into an array, including multi-stage variants

# Extract image names from compose files (image: <name> lines)
COMPOSE_IMAGES=$(printf '%s\n' "${COMPOSE_FILES[@]}" | while IFS= read -r f; do
# Explain: iterate each compose file for image lines
  grep -E "^[[:space:]]*image:[[:space:]]*" "$f" 2>/dev/null | sed -E 's/^[[:space:]]*image:[[:space:]]*([^[:space:]]+).*$/\1/' || true
# Explain: for each image line, strip to the image reference (repo[:tag])
done | sed '/^$/d' || true)
# Explain: after extraction remove any empty lines and tolerate missing matches

# Extract base images from Dockerfiles (FROM <name> ...)
DOCKERFILE_IMAGES=$(printf '%s\n' "${DOCKERFILES[@]}" | while IFS= read -r f; do
# Explain: iterate each Dockerfile to harvest base images in FROM instructions
  grep -E "^[[:space:]]*FROM[[:space:]]+" "$f" 2>/dev/null | awk '{print $2}' || true
# Explain: print the second token after FROM which is the image reference
done | sed '/^$/d' || true)
# Explain: after extraction remove any empty lines and tolerate missing matches

# Merge and unique the image list
IMAGES=$(printf '%s\n%s\n' "$COMPOSE_IMAGES" "$DOCKERFILE_IMAGES" | sed '/^$/d' | sort -u)
# Explain: combine compose and Dockerfile image names, drop empties, and unique them

# Preview the discovered images before deletion
step "Repository-defined images discovered"
# Explain: announce preview of images
if [ -n "$IMAGES" ]; then
# Explain: proceed only if there are images discovered
  echo "$IMAGES" | nl -w2 -s". "
  # Explain: print the list, numbered for readability
else
# Explain: handle case with no images discovered
  echo "No repository-defined images found."
  # Explain: print informational message when nothing discovered
fi
# Explain: end of preview

# Remove the discovered images if present locally
step "Removing repository-defined images"
# Explain: announce image removal phase
if [ -n "$IMAGES" ]; then
# Explain: proceed only if there are images discovered
  while IFS= read -r img; do
  # Explain: iterate over each image reference
    docker image rm -f "$img" >/dev/null 2>&1 || true
    # Explain: force-remove the image if present locally; ignore errors if absent or in-use
  done <<< "$IMAGES"
  # Explain: feed the list of images into the loop via here-string
fi
# Explain: end of conditional image removal

# Final pruning of dangling images and builder cache
step "Pruning dangling images and builder cache"
# Explain: announce final pruning step for completeness
docker image prune -f >/dev/null 2>&1 || true
# Explain: remove dangling images that may be left after deletions
docker builder prune -f >/dev/null 2>&1 || true
# Explain: clear builder cache layers to reclaim space

# Done
step "system docker cleaned ✅"
