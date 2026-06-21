#!/bin/bash
echo "🚀 Starting Jenkins Environment..."

# Ensure any existing Jenkins containers are removed completely
docker-compose -f docker-compose.jenkins.yml down

# Start Jenkins detached
docker-compose -f docker-compose.jenkins.yml up -d

echo ""
echo "⏳ Waiting 30 seconds for Jenkins to boot..."
sleep 30

echo ""
echo "📦 Installing Docker CLI and Docker Compose inside Jenkins container..."
docker exec -u root finsight-jenkins sh -c "apt-get update -qq && apt-get install -y -qq docker.io && curl -fsSL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-aarch64 -o /usr/bin/docker-compose && chmod +x /usr/bin/docker-compose && docker --version && docker-compose --version"

echo ""
echo "✅ Jenkins is fully ready!"
echo ""
echo "🔗 Access Jenkins at: http://localhost:8080"
echo "👤 Username: admin"
echo "🔑 Password: admin123"
