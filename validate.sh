#!/bin/bash
# Production Validation & Deployment Script
# Ensures system is production-ready

set -e

echo "🔍 MAYA SOC Enterprise - Production Validation"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Check Docker
echo "1️⃣  Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not installed${NC}"
    exit 1
fi
if ! docker ps &> /dev/null; then
    echo -e "${RED}❌ Docker daemon not running${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker ready${NC}"

# 2. Check Docker Compose
echo "2️⃣  Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose ready${NC}"

# 3. Check Python
echo "3️⃣  Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not installed${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | awk '{print $2}' | cut -d. -f1,2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION ready${NC}"

# 4. Validate .env file
echo "4️⃣  Validating .env..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env not found, creating from .env.example${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  UPDATE .env with production values before deploying!${NC}"
fi

# Check critical secrets
if grep -q "SECRET_KEY=$" .env || grep -q "SECRET_KEY=$\"\"" .env; then
    echo -e "${RED}❌ SECRET_KEY is empty in .env${NC}"
    echo "Generate: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    exit 1
fi
echo -e "${GREEN}✓ .env secrets configured${NC}"

# 5. Validate file structure
echo "5️⃣  Validating project structure..."
REQUIRED_FILES=(
    "backend/Dockerfile"
    "backend/requirements.txt"
    "backend/app/main.py"
    "backend/app/core/config.py"
    "backend/app/core/security.py"
    "backend/app/core/event_bus.py"
    "backend/app/api/v1/endpoints.py"
    "backend/app/models/event.py"
    "backend/app/models/incident.py"
    "frontend/Dockerfile"
    "docker-compose.yml"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ Missing: $file${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All required files present${NC}"

# 6. Check Python syntax
echo "6️⃣  Checking Python syntax..."
cd backend
python3 -m py_compile app/main.py app/core/config.py app/core/security.py app/core/event_bus.py \
    app/models/event.py app/models/incident.py app/api/v1/endpoints.py app/api/v1/websocket.py 2>/dev/null || {
    echo -e "${RED}❌ Python syntax errors found${NC}"
    exit 1
}
cd ..
echo -e "${GREEN}✓ Python syntax valid${NC}"

# 7. Check port availability
echo "7️⃣  Checking port availability..."
PORTS=(5173 8000 5432 6379 9092 8080)
for port in "${PORTS[@]}"; do
    if nc -z localhost $port 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Port $port already in use (stop existing containers)${NC}"
    fi
done
echo -e "${GREEN}✓ Port validation complete${NC}"

# 8. Validate docker-compose.yml
echo "8️⃣  Validating docker-compose.yml..."
docker-compose config > /dev/null 2>&1 || {
    echo -e "${RED}❌ docker-compose.yml is invalid${NC}"
    exit 1
}
echo -e "${GREEN}✓ docker-compose.yml valid${NC}"

# 9. Ready to deploy
echo ""
echo -e "${GREEN}✅ PRODUCTION VALIDATION PASSED${NC}"
echo ""
echo "Ready to deploy. Run:"
echo "  docker-compose up --build"
echo ""
echo "Then test:"
echo "  curl http://localhost:8000/health"
echo ""
