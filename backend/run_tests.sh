#!/bin/bash
# Setup and run tests using venv directly

cd /home/nahadi/Documents/Projects/DXHACK/backend

# Create venv if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Use venv pip directly to install dependencies
echo "Installing dependencies..."
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet -r requirements.txt

# Run integration tests using venv python
echo ""
echo "============================================"
echo "Running Integration Tests (Task 18)"
echo "============================================"
./venv/bin/python -m pytest test_integration.py -v --tb=short

# Run draft PR tests  
echo ""
echo "============================================"
echo "Running Draft PR Tests (Task 18.2)"
echo "============================================"
./venv/bin/python -m pytest test_draft_pr_generator.py -v --tb=short

echo ""
echo "Test execution complete!"
