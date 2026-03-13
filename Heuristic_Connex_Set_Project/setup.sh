##Unix-like Systems (Linux/macOS)
#!/bin/bash

# Create a virtual environment in the 'connexset' directory
python3 -m venv connexset

# Activate the virtual environment
source c/bin/activate

# Install dependencies from requirements.txt
pip install -r requirements.txt

echo "Virtual environment created and activated, dependencies installed."
