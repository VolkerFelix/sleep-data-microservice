#!/bin/bash

# Exit on error
set -e

echo "Setting up local SQLite database and running tests..."

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create a .env file for testing if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file for testing..."
    cp .env.example .env
fi

# Fix CORS_ORIGINS format to be a proper JSON array
echo "Fixing CORS_ORIGINS format in .env file..."
sed -i '' 's|CORS_ORIGINS=http://localhost:3000,http://localhost:8000|CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]|' .env

# Override DATABASE_URL to use SQLite for testing
echo "Setting DATABASE_URL to use SQLite..."
sed -i '' 's|DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sleep_data|DATABASE_URL=sqlite:///./data/test.db|' .env

# Create data directory if it doesn't exist
mkdir -p data

# Initialize the database with Alembic
echo "Initializing database with Alembic..."
alembic upgrade head

# Run the tests
echo "Running tests..."
pytest tests/ -v

echo "Setup and tests completed successfully!"
