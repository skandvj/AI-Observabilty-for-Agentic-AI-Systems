#!/bin/bash

# Indexing QA Setup Script
# This script automates the setup process for the Indexing QA system

set -e  # Exit on any error

echo "🚀 Setting up Indexing QA Observability Tool..."

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8+"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed. Please install Node.js 16+"
    exit 1
fi

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm is required but not installed. Please install npm"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Backend Setup
echo "🐍 Setting up Python backend..."

cd backend

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements/requirements.txt

echo "✅ Backend setup completed"

# Frontend Setup
echo "⚛️ Setting up React frontend..."

cd ../frontend

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Create environment file
echo "Creating environment configuration..."
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

echo "✅ Frontend setup completed"

# Return to root
cd ..

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Start the backend server:"
echo "   cd backend && source venv/bin/activate && python run_local.py"
echo ""
echo "2. Start the frontend server (in a new terminal):"
echo "   cd frontend && npm run dev"
echo ""
echo "3. Open your browser to: http://localhost:3001"
echo ""
echo "📚 For detailed instructions, see README.md"
echo "" 