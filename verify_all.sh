#!/bin/bash
set -e

echo "🔍 Starting Final System Verification..."

# Backend Verification
echo ""
echo "==============================================="
echo "🐍 Backend Verification"
echo "==============================================="
cd backend

# Check if venv exists but is broken (missing activate)
if [ -d "venv" ] && [ ! -f "venv/bin/activate" ]; then
    echo "⚠️  Found broken virtual environment. Removing..."
    rm -rf venv
fi

# Create virtual environment if missing
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    # Try creating venv, capture error if it fails
    if ! python3 -m venv venv; then
        echo ""
        echo "❌ Error: Failed to create virtual environment."
        echo "💡 Tip: You might need to install the venv package on Ubuntu:"
        echo "   sudo apt install python3-venv"
        echo ""
        exit 1
    fi
fi

# Activate and install
echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -q -r requirements.txt

# Run Tests
echo "Running Integration Tests..."
python -m pytest test_integration.py -v --tb=short

echo "Running Draft PR Generator Tests..."
python -m pytest test_draft_pr_generator.py -v --tb=short

# Frontend Verification
echo ""
echo "==============================================="
echo "⚛️ Frontend Verification"
echo "==============================================="
cd ../frontend

echo "Installing Node dependencies..."
npm install --silent

echo "Running Frontend Tests..."
npm run test

echo ""
echo "✅ All verifications passed successfully!"
