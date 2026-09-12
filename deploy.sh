#!/bin/bash
set -e

echo "=========================================="
echo " Starting SiteSync Backend Deployment "
echo "=========================================="

# Determine project directory path dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo " Current working directory: $(pwd)"

echo "--> 1. Pulling latest changes from git..."
git pull origin main

echo "--> 2. Building Docker image..."
docker build -t sitesync-backend -f backend/Dockerfile .

echo "--> 3. Stopping old container (if running)..."
docker stop sitesync-backend || true

echo "--> 4. Removing old container (if exists)..."
docker rm sitesync-backend || true

echo "--> 5. Starting new container..."
docker run -d \
  --name sitesync-backend \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file backend/.env \
  -e FRONTEND_URL=https://sitesync.vercel.app \
  sitesync-backend

echo "--> 6. Cleaning up dangling images to save disk space..."
docker image prune -f || true

echo "=========================================="
echo " Backend Deployment Completed Successfully!"
echo "=========================================="

docker ps --filter "name=sitesync-backend"
