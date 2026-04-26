#!/bin/bash
# Setup script for Agentic Newsroom

set -e

echo "🚀 Agentic Newsroom Setup"
echo "========================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "❌ Python 3 not found"; exit 1; }
echo "✓ Python 3 found"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Check yt-dlp
echo "Checking yt-dlp..."
yt-dlp --version > /dev/null || { echo "❌ yt-dlp not found"; exit 1; }
echo "✓ yt-dlp ready"
echo ""

# Setup .env
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - GEMINI_API_KEY"
    echo "   - GROQ_API_KEY"
    echo ""
else
    echo "✓ .env file exists"
    echo ""
fi

# Check API keys
if [ -f .env ]; then
    source .env
    if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your_gemini_api_key_here" ]; then
        echo "⚠️  GEMINI_API_KEY not configured in .env"
    else
        echo "✓ GEMINI_API_KEY configured"
    fi

    if [ -z "$GROQ_API_KEY" ] || [ "$GROQ_API_KEY" = "your_groq_api_key_here" ]; then
        echo "⚠️  GROQ_API_KEY not configured in .env"
    else
        echo "✓ GROQ_API_KEY configured"
    fi
fi

echo ""
echo "========================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys (if not done)"
echo "2. Run: python orchestrator.py --url 'https://youtube.com/watch?v=...'"
echo ""
echo "See QUICKSTART.md for detailed usage instructions."
