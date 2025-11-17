#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    SenSIt Setup Script                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "[*] Checking Python version..."
python3 --version

# Install dependencies
echo ""
echo "[*] Installing dependencies..."
pip3 install -r requirements.txt

# Make sensit.py executable
echo ""
echo "[*] Making sensit.py executable..."
chmod +x sensit.py

# Create reports directory
echo ""
echo "[*] Creating reports directory..."
mkdir -p reports

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    Setup Complete!                            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "1. Set your OpenAI API key:"
echo "   export OPENAI_API_KEY='your-key-here'"
echo ""
echo "2. Run SenSIt:"
echo "   python sensit.py --help"
echo "   python sensit.py --file test.txt"
echo ""
