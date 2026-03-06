#!/bin/bash
# Brain VPS Sync Script
# ====================
# Runs on VPS to pull latest Brain from GitHub

set -e

# Configuration
REPO_DIR="/root/brain"
GITHUB_REPO="https://github.com/vadymvertyan-stack/brain.git"
LOG_FILE="/var/log/brain_sync.log"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_success() {
    log "${GREEN}✓ $1${NC}"
}

log_error() {
    log "${RED}✗ $1${NC}"
}

# Check if repo exists
if [ ! -d "$REPO_DIR" ]; then
    log "Cloning Brain repository..."
    git clone "$GITHUB_REPO" "$REPO_DIR"
    log_success "Repository cloned"
else
    log "Pulling latest changes..."
    cd "$REPO_DIR"
    
    # Pull with fallback
    if git pull origin master --rebase; then
        log_success "Changes pulled successfully"
    else
        log_error "Pull failed, trying reset..."
        git fetch origin
        git reset --hard origin/master
        log_success "Repository reset to latest"
    fi
fi

# Log status
log "Current commit: $(git -C $REPO_DIR rev-parse --short HEAD 2>/dev/null || echo 'N/A')"
log "Last sync completed"
