#!/bin/bash

echo "🚀 Setting up Make It Heavy with Ollama..."
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed."
    echo "📥 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "✅ Ollama installed successfully!"
else
    echo "✅ Ollama is already installed."
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "🔄 Starting Ollama server..."
    ollama serve &
    sleep 3
    echo "✅ Ollama server started!"
else
    echo "✅ Ollama server is already running."
fi

# Check if the default model is installed
if ! ollama list | grep -q "llama3.2:3b"; then
    echo "📥 Pulling default model (llama3.2:3b)..."
    ollama pull llama3.2:3b
    echo "✅ Model downloaded successfully!"
else
    echo "✅ Default model is already installed."
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed!"

echo ""
echo "🎉 Setup complete! You can now run:"
echo "  python main.py          # Single agent mode"
echo "  python make_it_heavy.py # Multi-agent orchestrator mode"
echo ""
echo "💡 Make sure Ollama is running: ollama serve" 