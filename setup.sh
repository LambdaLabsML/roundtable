#!/bin/bash

echo "Setting up Roundtable..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env from template
if [ ! -f .env ]; then
    cp .env.template .env
    echo "Created .env file. Please add your API keys."
fi

# Create sessions directory
mkdir -p sessions

echo "Setup complete! Run 'python main.py' to start."
echo "Don't forget to add your API keys to the .env file!"