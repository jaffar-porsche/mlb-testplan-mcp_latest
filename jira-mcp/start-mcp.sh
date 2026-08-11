#!/bin/bash
set -e

echo "Starting Jira MCP Server..."

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

# Find suitable Python version (3.10+)
PYTHON_CMD=""
for cmd in python3.13 python3.12 python3.11 python3.10 python3 python; do
    if PYTHON_CMD=$(check_python_version "$cmd"); then
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python 3.10 or higher is required but not found"
    echo "Please install Python 3.10+ and ensure it's in your PATH"
    exit 1
fi

echo "Using Python: $PYTHON_CMD"
$PYTHON_CMD --version

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Remove old venv if created with wrong Python version
if [ -d "venv" ] && [ -f "venv/bin/python" ]; then
    venv_version=$(venv/bin/python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null) || true
    if [ -n "$venv_version" ]; then
        major=$(echo $venv_version | cut -d. -f1)
        minor=$(echo $venv_version | cut -d. -f2)
        if [ "$major" -ne 3 ] || [ "$minor" -lt 10 ]; then
            echo "Removing old virtual environment (Python $venv_version < 3.10)..."
            rm -rf venv
        fi
    fi
fi

# Create venv if it doesn't exist
VENV_CREATED=false
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    VENV_CREATED=true
fi

source venv/bin/activate

# Install dependencies on first run or when requirements change
if [ "$VENV_CREATED" = true ] || [ "requirements.txt" -nt "venv/.installed" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    touch venv/.installed
fi

# Read port from .env or default
PORT=8000
if [ -f ".env" ]; then
    MCP_PORT_LINE=$(grep -E '^MCP_PORT[ ]*=' .env | tail -n 1)
    if [ -n "$MCP_PORT_LINE" ]; then
        PORT=$(echo "$MCP_PORT_LINE" | cut -d'=' -f2 | tr -d ' ')
    fi
fi

echo "Starting server on http://localhost:$PORT/mcp/"
echo "API docs available at http://localhost:$PORT/docs"
echo "Press Ctrl+C to stop"

uvicorn mcp_server:app --host 0.0.0.0 --port $PORT --reload
