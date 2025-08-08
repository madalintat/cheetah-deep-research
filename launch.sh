#!/bin/bash

echo "🚀 Launching Make It Heavy - AI Research Platform"
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "❌ Ollama is not running. Please start it first:"
    echo "   ollama serve"
    exit 1
fi

echo "✅ Ollama is running"

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "👋 Goodbye!"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend
echo "🔧 Starting FastAPI backend..."
python3 backend.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend started successfully
if ! curl -s http://localhost:8000/health &> /dev/null; then
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Backend running on http://localhost:8000"

# Start frontend
echo "🎨 Starting React frontend..."
cd frontend
npm install --silent
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 5

if ! curl -s http://localhost:5173 &> /dev/null; then
    echo "❌ Frontend failed to start"
    cleanup
    exit 1
fi

echo "✅ Frontend running on http://localhost:5173"
echo ""
echo "🎉 Make It Heavy is ready!"
echo "📱 Open your browser to: http://localhost:5173"
echo "🔗 API available at: http://localhost:8000"
echo ""
echo "💡 Press Ctrl+C to stop all servers"

# Keep the script running
wait
