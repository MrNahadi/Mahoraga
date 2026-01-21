#!/bin/bash
# Run integration tests for Mahoraga backend

cd /home/nahadi/Documents/Projects/DXHACK/backend
./venv/bin/python -m pytest test_integration.py -v --tb=short
