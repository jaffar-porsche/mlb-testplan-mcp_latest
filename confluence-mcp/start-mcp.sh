#!/bin/bash
set -e

echo "🚀 Starting Confluence MCP Server..."

# Function to check Python version
check_python_version() {
    local python_cmd=$1
    if command -v "$python_cmd" &> /dev/null; then
        local version=$($python_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        if [ $? -eq 0 ]; then
            local major=$(echo $version | cut -d. -f1)
            local minor=$(echo $version | cut -d. -f2)
            if [ "$major" -eq 3 ] && [ "$minor" -ge 10 ]; then
                echo "$python_cmd"
                return 0
            fi
        fi
    fi
    return 1
}

# Function to detect OS
detect_os() {
    if [ -f /etc/debian_version ]; then
        echo "debian"
    elif [ -f /etc/redhat-release ]; then
        echo "redhat"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# Find suitable Python version (3.10+)
PYTHON_CMD=""
for cmd in python3.13 python3.12 python3.11 python3.10 python3 python; do
    if PYTHON_CMD=$(check_python_version "$cmd"); then
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Python 3.10 or higher is required but not found"
    echo "💡 Please install Python 3.10+ and ensure it's in your PATH"
    echo "💡 fastapi-mcp requires Python 3.10 or higher"
    exit 1
fi

echo "🐍 Using Python: $PYTHON_CMD"
$PYTHON_CMD --version

# Check for venv dependencies on Debian/Ubuntu systems
OS_TYPE=$(detect_os)
if [ "$OS_TYPE" = "debian" ]; then
    PYTHON_VERSION_SHORT=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    VENV_PACKAGE="python${PYTHON_VERSION_SHORT}-venv"
    
    echo "🔍 Checking for venv package on Debian/Ubuntu system..."
    if ! dpkg -l | grep -q "$VENV_PACKAGE"; then
        echo "⚠️  Missing required package: $VENV_PACKAGE"
        echo "💡 Installing $VENV_PACKAGE..."
        
        if command -v sudo &> /dev/null; then
            sudo apt update && sudo apt install -y "$VENV_PACKAGE"
        else
            echo "❌ sudo not available. Please run manually:"
            echo "   apt update && apt install -y $VENV_PACKAGE"
            exit 1
        fi
        
        if [ $? -ne 0 ]; then
            echo "❌ Failed to install $VENV_PACKAGE"
            echo "💡 Please run manually: sudo apt install $VENV_PACKAGE"
            exit 1
        fi
        echo "✅ Successfully installed $VENV_PACKAGE"
    else
        echo "✅ $VENV_PACKAGE is already installed"
    fi
fi

# Remove old venv if it exists and was created with wrong Python version
VENV_RECREATED=false
if [ -d "venv" ]; then
    echo "🔍 Checking existing virtual environment..."
    if [ -f "venv/bin/python" ]; then
        venv_version=$(venv/bin/python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        if [ $? -eq 0 ]; then
            major=$(echo $venv_version | cut -d. -f1)
            minor=$(echo $venv_version | cut -d. -f2)
            if [ "$major" -ne 3 ] || [ "$minor" -lt 10 ]; then
                echo "🗑️  Removing old virtual environment (Python $venv_version < 3.10)..."
                rm -rf venv
                VENV_RECREATED=true
            else
                echo "✅ Existing virtual environment uses Python $venv_version (compatible)"
            fi
        else
            echo "🗑️  Removing corrupted virtual environment..."
            rm -rf venv
            VENV_RECREATED=true
        fi
    fi
fi

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment with $PYTHON_CMD..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        if [ "$OS_TYPE" = "debian" ]; then
            echo "💡 If you see an 'ensurepip' error, try:"
            echo "   sudo apt install python${PYTHON_VERSION_SHORT}-venv"
        fi
        exit 1
    fi
    echo "✅ Virtual environment created successfully"
    VENV_RECREATED=true
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    # Windows Git Bash compatibility - handle line ending issues
    if command -v dos2unix &> /dev/null; then
        dos2unix venv/Scripts/activate 2>/dev/null || true
    fi
    source venv/Scripts/activate 2>/dev/null || {
        echo "⚠️  Line ending issue detected, trying alternative activation..."
        # Alternative activation for Windows environments
        export PATH="$(pwd)/venv/Scripts:$PATH"
        export VIRTUAL_ENV="$(pwd)/venv"
        export PYTHONPATH=""
        echo "✅ Virtual environment activated (alternative method)"
    }
else
    echo "❌ Cannot find activation script in venv"
    echo "💡 Try deleting the venv folder and running the script again"
    echo "💡 Or use the Windows batch file: start-mcp.bat"
    exit 1
fi

# Upgrade pip and install requirements
if [ "$VENV_RECREATED" = true ]; then
    echo "📥 Installing dependencies..."
    pip install --upgrade pip
    if [ -f "requirements.txt" ]; then
        echo "📦 Installing from requirements.txt..."
        pip install -r requirements.txt
    else
        echo "📦 requirements.txt not found, installing default packages..."
        pip install fastapi-mcp fastapi httpx uvicorn atlassian-python-api python-dotenv pydantic
    fi
fi

# Check if .env file exists

# Read MCP_Port from .env or .env.example
PORT=8001
if [ -f ".env" ]; then
    MCP_PORT_LINE=$(grep -E '^MCP_Port[ ]*=' .env | tail -n 1)
    if [ -n "$MCP_PORT_LINE" ]; then
        PORT=$(echo "$MCP_PORT_LINE" | cut -d'=' -f2 | tr -d ' ')
    fi
else
    MCP_PORT_LINE=$(grep -E '^MCP_Port[ ]*=' .env.example | tail -n 1)
    if [ -n "$MCP_PORT_LINE" ]; then
        PORT=$(echo "$MCP_PORT_LINE" | cut -d'=' -f2 | tr -d ' ')
    fi
    echo "⚠️  Warning: .env file not found"
    echo "💡 Copy .env.example to .env and add your CONFLUENCE_PAT"
    exit 1
fi

echo "🌟 Starting server on http://localhost:$PORT/mcp/"
echo "📖 API docs available at http://localhost:$PORT/docs"
echo "🛑 Press Ctrl+C to stop"

# Start the MCP server
uvicorn mcp_server:app --host 0.0.0.0 --port $PORT --reload
