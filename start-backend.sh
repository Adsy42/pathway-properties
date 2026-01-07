#!/bin/bash
# Start Pathway Property Backend

cd "$(dirname "$0")/backend"

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

source venv/bin/activate

echo "🚀 Starting Pathway Property Backend..."
echo "📍 API will be available at http://localhost:8000"
echo "📖 API docs at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn main:app --reload --port 8000







