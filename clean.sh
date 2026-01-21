#!/bin/bash
set -e

echo "🧹 Starting Project Cleanup..."

# Remove log files
echo "Removing log files..."
find . -type f -name "*.log" -delete

# Remove Python cache directories
echo "Removing __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} +

# Remove pytest cache
echo "Removing .pytest_cache directories..."
find . -type d -name ".pytest_cache" -exec rm -rf {} +

# Remove hypothesis cache
echo "Removing .hypothesis directories..."
find . -type d -name ".hypothesis" -exec rm -rf {} +

# Remove temporary test databases
echo "Removing temporary test databases..."
find . -type f -name "test_*.db" -delete

# Remove completion summary artifact
if [ -f "COMPLETION_SUMMARY.md" ]; then
    echo "Removing COMPLETION_SUMMARY.md..."
    rm COMPLETION_SUMMARY.md
fi

echo "✅ Project cleanup complete!"
