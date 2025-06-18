#!/bin/bash

echo "Setting up Ontario Harness Racing Analytics Suite..."

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend
pip install -r requirements.txt

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd ../frontend
npm install

echo "Setup complete!"
echo ""
echo "To start the application:"
echo "1. Start the backend: cd backend && python main.py"
echo "2. Start the frontend: cd frontend && npm start"