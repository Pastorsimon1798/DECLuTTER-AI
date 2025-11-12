#!/bin/bash

# MutualCircle Launch Script
# This script helps you launch the MutualCircle application from your desktop

# Don't exit on error - we want to handle installations
set +e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   MutualCircle Launch Script          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Homebrew if missing
install_homebrew() {
    if ! command_exists brew; then
        echo -e "${YELLOW}📦 Homebrew not found. Installing Homebrew...${NC}"
        echo -e "${YELLOW}This will require your password.${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH for Apple Silicon Macs
        if [ -f "/opt/homebrew/bin/brew" ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
        
        if ! command_exists brew; then
            echo -e "${RED}❌ Failed to install Homebrew. Please install manually from https://brew.sh${NC}"
            exit 1
        fi
        echo -e "${GREEN}✅ Homebrew installed${NC}"
    fi
}

# Function to install Docker
install_docker() {
    # First check if Docker is already available (maybe installed but not in PATH)
    if [ -f "/Applications/Docker.app/Contents/Resources/bin/docker" ]; then
        export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
    fi
    
    if ! command_exists docker; then
        echo -e "${YELLOW}🐳 Docker not found. Installing Docker Desktop...${NC}"
        
        if command_exists brew; then
            echo -e "${BLUE}Installing Docker Desktop via Homebrew (this may take a few minutes)...${NC}"
            echo -e "${YELLOW}Note: You may see some warnings about existing binaries - that's okay.${NC}"
            
            # Try to install Docker
            INSTALL_OUTPUT=$(brew install --cask docker 2>&1)
            INSTALL_STATUS=$?
            
            # Check for binary conflict errors
            if echo "$INSTALL_OUTPUT" | grep -q "Error: It seems there is already a Binary"; then
                echo -e "${YELLOW}⚠️  Installation conflict detected. Attempting to fix...${NC}"
                # Try to remove the conflicting binary and retry
                if [ -f "/usr/local/bin/hub-tool" ]; then
                    echo -e "${YELLOW}Removing conflicting binary (may require password)...${NC}"
                    sudo rm -f /usr/local/bin/hub-tool 2>/dev/null || true
                    echo -e "${BLUE}Retrying Docker installation...${NC}"
                    brew install --cask docker
                    INSTALL_STATUS=$?
                fi
            fi
            
            # Check if Docker app was installed even if there were warnings
            if [ -d "/Applications/Docker.app" ]; then
                echo -e "${GREEN}✅ Docker Desktop installed${NC}"
                # Add Docker to PATH
                export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
            else
                echo -e "${YELLOW}⚠️  Docker installation had some issues, but let's check if it's available...${NC}"
            fi
            
            # Check again if docker command is now available
            if [ -f "/Applications/Docker.app/Contents/Resources/bin/docker" ]; then
                export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
            fi
            
            if command_exists docker; then
                echo -e "${GREEN}✅ Docker command is available${NC}"
            else
                echo -e "${YELLOW}⚠️  Docker may need to be started first. Let's try...${NC}"
            fi
        else
            echo -e "${RED}❌ Docker is not installed and Homebrew is not available.${NC}"
            echo -e "${YELLOW}Please install Docker Desktop manually:${NC}"
            echo -e "${BLUE}https://www.docker.com/products/docker-desktop/${NC}"
            echo -e "${YELLOW}Or install Homebrew first: https://brew.sh${NC}"
            exit 1
        fi
    fi
    
    # Check if Docker Desktop app exists
    if [ -d "/Applications/Docker.app" ]; then
        # Add Docker to PATH if not already there
        if [ -f "/Applications/Docker.app/Contents/Resources/bin/docker" ]; then
            export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
        fi
    else
        echo -e "${RED}❌ Docker Desktop app not found in Applications.${NC}"
        echo -e "${YELLOW}Please install Docker Desktop manually:${NC}"
        echo -e "${BLUE}https://www.docker.com/products/docker-desktop/${NC}"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Docker is not running. Starting Docker Desktop...${NC}"
        open -a Docker 2>/dev/null || echo -e "${YELLOW}Please start Docker Desktop manually from Applications.${NC}"
        echo -e "${YELLOW}Waiting for Docker to start (this may take 30-60 seconds)...${NC}"
        
        # Wait up to 60 seconds for Docker to start
        for i in {1..60}; do
            if docker info >/dev/null 2>&1; then
                echo -e "${GREEN}✅ Docker is running${NC}"
                return 0
            fi
            sleep 1
            if [ $((i % 10)) -eq 0 ]; then
                echo -n "."
            fi
        done
        echo ""
        echo -e "${YELLOW}⚠️  Docker Desktop is starting but not ready yet.${NC}"
        echo -e "${YELLOW}Please wait for Docker Desktop to fully start (check the menu bar icon),${NC}"
        echo -e "${YELLOW}then run this script again.${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ Docker is running${NC}"
    fi
}

# Function to install Python
install_python() {
    if ! command_exists python3; then
        echo -e "${YELLOW}🐍 Python 3 not found. Installing Python...${NC}"
        
        if command_exists brew; then
            brew install python@3.11
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ Python installed${NC}"
            else
                echo -e "${RED}❌ Failed to install Python. Please install manually.${NC}"
                exit 1
            fi
        else
            echo -e "${RED}❌ Python 3 is not installed and Homebrew is not available.${NC}"
            echo -e "${YELLOW}Please install Python 3.11+ from: https://www.python.org/downloads/${NC}"
            exit 1
        fi
    fi
}

# Function to install Node.js
install_nodejs() {
    if ! command_exists node; then
        echo -e "${YELLOW}📦 Node.js not found. Installing Node.js...${NC}"
        
        if command_exists brew; then
            brew install node@18
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ Node.js installed${NC}"
                # Add to PATH
                export PATH="/opt/homebrew/opt/node@18/bin:$PATH"
            else
                echo -e "${RED}❌ Failed to install Node.js. Please install manually.${NC}"
                exit 1
            fi
        else
            echo -e "${RED}❌ Node.js is not installed and Homebrew is not available.${NC}"
            echo -e "${YELLOW}Please install Node.js 18+ from: https://nodejs.org/${NC}"
            exit 1
        fi
    fi
    
    # Check npm
    if ! command_exists npm; then
        echo -e "${YELLOW}📦 npm not found. This usually comes with Node.js.${NC}"
        if command_exists brew; then
            brew install npm
        else
            echo -e "${RED}❌ npm is not available. Please reinstall Node.js.${NC}"
            exit 1
        fi
    fi
}

# Function to check and install prerequisites
check_prerequisites() {
    echo -e "${BLUE}Checking prerequisites...${NC}"
    echo ""
    
    # Install Homebrew first if needed (it helps install other things)
    install_homebrew
    
    # Check and install Python
    if ! command_exists python3; then
        install_python
    else
        echo -e "${GREEN}✅ Python 3 found${NC}"
    fi
    
    # Check and install Node.js
    if ! command_exists node || ! command_exists npm; then
        install_nodejs
    else
        echo -e "${GREEN}✅ Node.js found${NC}"
        echo -e "${GREEN}✅ npm found${NC}"
    fi
    
    # Check and install Docker
    install_docker
    
    echo ""
    echo -e "${GREEN}✅ All prerequisites are ready!${NC}"
    echo ""
}

# Function to setup backend
setup_backend() {
    echo -e "${BLUE}Setting up backend...${NC}"
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating Python virtual environment...${NC}"
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    if [ ! -f "venv/.deps_installed" ]; then
        echo -e "${YELLOW}Installing Python dependencies...${NC}"
        pip install --upgrade pip
        pip install -r requirements.txt
        touch venv/.deps_installed
    fi
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
        cat > .env << EOF
# Application Configuration
APP_NAME=CommunityCircle
DEBUG=True
ENVIRONMENT=development
API_V1_PREFIX=/api

# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:devpass@localhost:5432/communitycircle
DATABASE_URL_SYNC=postgresql://postgres:devpass@localhost:5432/communitycircle

# Security - Generate a secure key: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Redis
REDIS_URL=redis://localhost:6379/0

# Optional: SMS (Plivo)
PLIVO_AUTH_ID=
PLIVO_AUTH_TOKEN=
PLIVO_PHONE_NUMBER=

# Optional: Email (Brevo)
BREVO_API_KEY=
BREVO_SENDER_EMAIL=noreply@communitycircle.org
BREVO_SENDER_NAME=CommunityCircle

# Optional: 211 API
TWO11_API_KEY=
TWO11_API_URL=https://api.211.org

# Frontend URL
FRONTEND_URL=http://localhost:5173

# Optional: Monitoring
SENTRY_DSN=
POSTHOG_API_KEY=
EOF
        echo -e "${GREEN}✅ Created .env file with default values${NC}"
    fi
    
    cd ..
    echo -e "${GREEN}✅ Backend setup complete${NC}"
    echo ""
}

# Function to setup frontend
setup_frontend() {
    echo -e "${BLUE}Setting up frontend...${NC}"
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing npm dependencies...${NC}"
        npm install
    fi
    
    cd ..
    echo -e "${GREEN}✅ Frontend setup complete${NC}"
    echo ""
}

# Function to start services
start_services() {
    echo -e "${BLUE}Starting services...${NC}"
    
    # Start Docker services (PostgreSQL and Redis)
    echo -e "${YELLOW}Starting Docker containers (PostgreSQL & Redis)...${NC}"
    docker-compose up -d
    
    # Wait for database to be ready
    echo -e "${YELLOW}Waiting for database to be ready...${NC}"
    sleep 5
    
    # Run migrations
    echo -e "${YELLOW}Running database migrations...${NC}"
    cd backend
    source venv/bin/activate
    alembic upgrade head
    cd ..
    
    echo -e "${GREEN}✅ Services started${NC}"
    echo ""
}

# Function to start application
start_app() {
    echo -e "${BLUE}Starting MutualCircle application...${NC}"
    echo ""
    
    # Create a function to cleanup on exit
    cleanup() {
        echo ""
        echo -e "${YELLOW}Shutting down...${NC}"
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
        exit 0
    }
    
    trap cleanup SIGINT SIGTERM
    
    # Start backend
    echo -e "${GREEN}🚀 Starting backend server on http://localhost:8000${NC}"
    cd backend
    source venv/bin/activate
    python -m app.main &
    BACKEND_PID=$!
    cd ..
    
    # Wait a bit for backend to start
    sleep 3
    
    # Start frontend
    echo -e "${GREEN}🚀 Starting frontend server on http://localhost:5173${NC}"
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   MutualCircle is running!            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Frontend:${NC} http://localhost:5173"
    echo -e "${BLUE}Backend API:${NC} http://localhost:8000"
    echo -e "${BLUE}API Docs:${NC} http://localhost:8000/api/docs"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop the application${NC}"
    echo ""
    
    # Wait for processes
    wait $BACKEND_PID $FRONTEND_PID
}

# Main execution
main() {
    # Re-enable exit on error for the main execution
    set -e
    
    check_prerequisites
    setup_backend
    setup_frontend
    start_services
    start_app
}

# Run main function
main

