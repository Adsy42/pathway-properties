#!/bin/bash
# Start Pathway Property Frontend

cd "$(dirname "$0")/frontend"

if [ ! -d "node_modules" ]; then
    echo "❌ Dependencies not installed. Run ./setup.sh first."
    exit 1
fi

echo "🚀 Starting Pathway Property Frontend..."
echo "📍 App will be available at http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

npm run dev







