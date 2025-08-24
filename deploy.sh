#!/bin/bash

# Deployment script for GPT-OSS AI Operating System

# Configuration
DOCKER_COMPOSE_FILE="docker-compose.yml"
REMOTE_USER="aios"
REMOTE_HOST="production.example.com"
REMOTE_DIR="/opt/gpt-oss"
BACKUP_DIR="$REMOTE_DIR/backups"
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# Validate environment
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed"
    exit 1
fi

# Create backup of current deployment
ssh $REMOTE_USER@$REMOTE_HOST "
    mkdir -p $BACKUP_DIR/$TIMESTAMP && \
    cp $REMOTE_DIR/docker-compose.yml $BACKUP_DIR/$TIMESTAMP/ && \
    docker-compose -f $REMOTE_DIR/docker-compose.yml logs > $BACKUP_DIR/$TIMESTAMP/logs.txt
"

# Stop existing services
ssh $REMOTE_USER@$REMOTE_HOST "
    cd $REMOTE_DIR && \
    docker-compose down
"

# Copy new compose file
scp $DOCKER_COMPOSE_FILE $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/

# Pull latest images and start services
ssh $REMOTE_USER@$REMOTE_HOST "
    cd $REMOTE_DIR && \
    docker-compose pull && \
    docker-compose up -d
"

# Verify deployment
ssh $REMOTE_USER@$REMOTE_HOST "
    cd $REMOTE_DIR && \
    docker-compose ps && \
    echo "Deployment completed successfully at $(date)"
"