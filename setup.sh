#!/bin/bash

echo "Setting up project environment..."

# Check if nvm exists, install if not
if [ ! -d "$HOME/.nvm" ]; then
  echo "Installing nvm..."
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
fi

# Load nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Install latest Node.js and update npm
echo "Setting up Node.js environment..."
nvm install node
nvm use node
npm install -g npm

# Upgrade pip
pip install --upgrade pip

echo "Installing Python dependencies..."

# Install base dependencies first
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# For gradio components
python -m venv gradio_env
source gradio_env/bin/activate
pip install -r requirements.txt -r requirements_gradio.txt

# For opea components
python -m venv opea_env
source opea_env/bin/activate
pip install -r requirements.txt -r requirements_opea.txt

echo "✅ Setup complete! Node.js and Python dependencies installed."
