#!/bin/bash
# Fix line ending issues in Windows virtual environment

echo "🔧 Fixing Windows line ending issues..."

if [ ! -d "venv" ]; then
    echo "❌ No virtual environment found"
    exit 1
fi

# Check if we're in a Windows environment with Unix shell
if [ -f "venv/Scripts/activate" ]; then
    echo "📝 Found Windows virtual environment"
    
    # Try to fix line endings
    if command -v dos2unix &> /dev/null; then
        echo "🔄 Converting line endings with dos2unix..."
        dos2unix venv/Scripts/activate 2>/dev/null
        dos2unix venv/Scripts/activate.bat 2>/dev/null
        echo "✅ Line endings converted"
    elif command -v sed &> /dev/null; then
        echo "🔄 Converting line endings with sed..."
        sed -i 's/\r$//' venv/Scripts/activate 2>/dev/null
        echo "✅ Line endings converted"
    else
        echo "⚠️  Cannot automatically fix line endings"
        echo "💡 Recommended solutions:"
        echo "   1. Use start-mcp.bat instead of start-mcp.sh"
        echo "   2. Install dos2unix: apt-get install dos2unix"
        echo "   3. Delete venv folder and recreate in native environment"
        exit 1
    fi
    
    echo "🧪 Testing activation..."
    source venv/Scripts/activate && echo "✅ Activation successful" || {
        echo "❌ Still having issues"
        echo "💡 Try: rm -rf venv && ./setup.sh"
    }
else
    echo "✅ Unix virtual environment, no line ending issues"
fi

echo "🎉 Fix completed!"
