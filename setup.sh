#!/bin/bash
# setup.sh

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

# Activate Python virtual environment if it exists
if [ -d "venv" ]; then
  echo "Activating virtual environment..."
  source venv/bin/activate
else
  echo "Creating virtual environment..."
  python -m venv venv
  source venv/bin/activate
fi

# Upgrade pip
pip install --upgrade pip

# Install pandas with binary-only option to avoid compilation issues
pip install --only-binary=pandas pandas==2.2.3

# Install all other dependencies from requirements.txt
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "✅ Setup complete! Node.js and Python dependencies installed."