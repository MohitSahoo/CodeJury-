#!/bin/bash
# Setup script for Security Audit Pipeline
# Multi-agent AI security analysis for your commits.

set -e

echo "🚀 Security Audit Pipeline Setup"
echo "================================"
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

# Setup .env
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - GEMINI_API_KEY (Required for Agent A)"
    echo "   - GROQ_API_KEY (Required for Agent B)"
    echo ""
else
    echo "✓ .env file exists"
    echo ""
fi

# Install pre-commit hook
echo "Checking for git repository..."
if [ -d .git ]; then
    echo "Installing pre-commit hooks..."
    pre-commit install
    echo "✓ Pre-commit hooks installed"
else
    echo "⚠️  Not a git repository. Skipping pre-commit installation."
    echo "   Run 'git init' and 'pre-commit install' manually later."
fi
echo ""

# Check API keys
if [ -f .env ]; then
    # Use grep to check for keys instead of sourcing (safer for script)
    if grep -q "GEMINI_API_KEY=your_" .env || ! grep -q "GEMINI_API_KEY=" .env; then
        echo "⚠️  GEMINI_API_KEY not configured in .env"
    else
        echo "✓ GEMINI_API_KEY configured"
    fi

    if grep -q "GROQ_API_KEY=your_" .env || ! grep -q "GROQ_API_KEY=" .env; then
        echo "⚠️  GROQ_API_KEY not configured in .env"
    else
        echo "✓ GROQ_API_KEY configured"
    fi
fi

echo ""
echo "================================"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
| 1. Ensure your API keys are in .env
| 2. Stage some files: git add path/to/file.py
| 3. Run audit: python3 security_audit.py
| 
| See USAGE.md for detailed instructions.
echo ""
