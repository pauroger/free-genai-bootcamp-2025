#!/bin/bash

# Clean up any existing overmind sockets
if [ -e ./.overmind.sock ]; then
  echo "Removing existing Overmind socket..."
  rm ./.overmind.sock
fi

# Check if Docker is running
if docker info > /dev/null 2>&1; then
    echo "Docker is running - starting full system"
    
    # Start Docker services (use detached mode)
    cd opea-comps
    export LLM_ENDPOINT_PORT=9000
    echo "Starting Docker containers in detached mode..."
    docker compose up -d
    
    echo "Waiting for Docker containers to initialize (30 seconds)..."
    sleep 30
    
    echo "Pulling model..."
    curl http://localhost:9000/api/pull -d '{"model": "llama3.2:1b"}'
    
    # Go back to project root
    cd ..
    
    # Start ALL services with a single overmind command
    echo "Starting all services..."
    overmind start -f Procfile.all
    
    # Clean up Docker when done
    echo "Shutting down Docker containers..."
    cd opea-comps
    docker compose down
    cd ..
else
    echo "Docker is not running - starting core services only"
    
    # Start only core services
    overmind start -f Procfile
fi