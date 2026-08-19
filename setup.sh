#!/bin/bash

# Exit on error
set -e

echo "Setting up the environment for Motivation-Post..."

# Clean up previous generated posters
if [ -d "posters" ]; then
    echo "Cleaning up previous 'posters' directory..."
    rm -rf posters
fi

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment '.venv'..."
    python3 -m venv .venv
else
    echo "Virtual environment '.venv' already exists."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install required dependencies
echo "Installing dependencies (requests, pillow, python-dotenv)..."
pip install --upgrade pip
pip install requests pillow python-dotenv

# Set up .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "No .env file found. Let's set up your environment variables."
    echo "You can get your API key directly from: https://enter.pollinations.ai/keys"
    read -p "Enter your POLLINATIONS_API_KEY (or press Enter to skip): " api_key
    if [ -n "$api_key" ]; then
        echo "POLLINATIONS_API_KEY=\"$api_key\"" > .env
        echo ".env file created with your API key."
    else
        echo "Skipped setting POLLINATIONS_API_KEY. You can add it later to the .env file."
    fi
else
    echo ""
    echo ".env file already exists."
fi

echo ""
echo "Setup complete!"
echo ""
echo "To start using the script, run:"
echo "  source .venv/bin/activate"
echo "  python quote_poster.py"
