#!/bin/bash

# Define colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}    Starting FinSight Platform (Docker)       ${NC}"
echo -e "${GREEN}===============================================${NC}\n"

# Navigate to project root just in case
cd /Users/gauravkulkarni/Desktop/Devops_financialRisk

echo -e "${BLUE}Stopping any existing containers...${NC}"
docker-compose down

echo -e "\n${YELLOW}Building and starting all containers (Frontend, Analytics API, Risk Engine)...${NC}"
echo -e "${BLUE}This may take a moment to build the images...${NC}\n"

# Start the containers
docker-compose up -d --build

echo -e "\n${GREEN}===============================================${NC}"
echo -e "${GREEN}           Containers Started!                 ${NC}"
echo -e "${GREEN}===============================================${NC}\n"

# Show the running containers
docker-compose ps

echo -e "\n${BLUE}Access the application at:${NC}"
echo -e "Frontend Dashboard : http://localhost:5173"
echo -e "Analytics API      : http://localhost:8000"
echo -e "Risk Engine        : http://localhost:8001"

echo -e "\n${YELLOW}To view live logs, run: ${NC}docker-compose logs -f"
echo -e "${YELLOW}To stop the platform, run: ${NC}docker-compose down\n"
