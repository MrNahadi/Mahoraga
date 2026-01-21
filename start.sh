#!/bin/bash

# Function to handle cleanup on exit
cleanup() {
    echo "Stopping all services..."
    kill $(jobs -p) 2>/dev/null
}

trap cleanup EXIT INT TERM

echo "🚀 Starting Mahoraga System..."

# Start Backend
echo "🐍 Starting Backend..."
cd backend || exit
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run uvicorn in background
python -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Start Frontend
echo "⚛️ Starting Frontend..."
cd frontend || exit
if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install --silent
fi
npm run dev -- --host &
FRONTEND_PID=$!
cd ..

echo "✅ System running!"
echo "   Backend: http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo "   Press Ctrl+C to stop"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
