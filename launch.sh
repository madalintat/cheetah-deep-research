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

# Start backend (reuse existing if bound)
echo "🔧 Starting FastAPI backend..."
if lsof -i :8000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "ℹ️  Backend already running on :8000"
  BACKEND_PID=""
else
  uvicorn backend:app --host 0.0.0.0 --port 8000 --reload &
  BACKEND_PID=$!
fi

# Wait for backend to start
sleep 3

# Check if backend started successfully (or was already running)
if ! curl -s http://localhost:8000/health &> /dev/null; then
    echo "❌ Backend not responding on :8000/health"
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null || true
    exit 1
fi

echo "✅ Backend running on http://localhost:8000"

# Start frontend
echo "🎨 Starting React frontend..."
cd frontend
npm install --silent
# If 5173 is taken, vite chooses another; we still track PID
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 5

echo "✅ Frontend dev server started (check terminal for actual port)"
echo ""
echo "🎉 Make It Heavy is ready!"
echo "📱 Open your browser to: http://localhost:5173"
echo "🔗 API available at: http://localhost:8000"
echo ""
echo "💡 Press Ctrl+C to stop all servers"

# Keep the script running
wait
