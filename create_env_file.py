#!/usr/bin/env python3
"""
Script to create .env file with all required environment variables.
Run this to set up your environment configuration.
"""

import os

def create_env_file():
    """Create .env file with the provided configuration"""
    
    env_content = """# ===========================================
# MAKE IT HEAVY - ENVIRONMENT VARIABLES
# ===========================================
# 🚨 KEEP THIS FILE SECURE - DO NOT COMMIT TO GIT
# Add this file to .gitignore to prevent accidental commits

# Supabase Configuration
SUPABASE_URL=https://xkooxszqjcvpsxrdroez.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhrb294c3pxamN2cHN4cmRyb2V6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDE1MzU3MCwiZXhwIjoyMDY5NzI5NTcwfQ.dtW9Ywlic_hTuXiOz4VOVwaa1m2uROvj3jCVFdZ0taA
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhrb294c3pxamN2cHN4cmRyb2V6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQxNTM1NzAsImV4cCI6MjA2OTcyOTU3MH0.CGOTYLv67aHwMsVCOV_SbYCLZov9_iS-HASJHHEIMY4

# Tavily API Configuration (for web search fallback)
TAVILY_API_KEY=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

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Development Settings
NODE_ENV=development
DEBUG=true

# Optional: Add your own custom environment variables below
# CUSTOM_API_KEY=your_key_here
# CUSTOM_SECRET=your_secret_here
"""

    env_example_content = """# ===========================================
# MAKE IT HEAVY - ENVIRONMENT VARIABLES (EXAMPLE)
# ===========================================
# Copy this file to .env and fill in your actual values

# Supabase Configuration
# Get these from: https://supabase.com/dashboard/project/YOUR_PROJECT/settings/api
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key_here
SUPABASE_ANON_KEY=your_anon_key_here

# Tavily API Configuration (for web search fallback)
# Get from: https://tavily.com/
TAVILY_API_KEY=tvly-your-api-key-here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Development Settings
NODE_ENV=development
DEBUG=true

# Optional: Add your own custom environment variables below
# CUSTOM_API_KEY=your_key_here
# CUSTOM_SECRET=your_secret_here
"""

    try:
        # Create .env file
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with all API keys and secrets")
        
        # Create .env.example file
        with open('.env.example', 'w') as f:
            f.write(env_example_content)
        print("✅ Created .env.example file as template")
        
        # Check if .env is in .gitignore
        gitignore_path = '.gitignore'
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r') as f:
                gitignore_content = f.read()
            
            if '.env' in gitignore_content:
                print("✅ .env is already in .gitignore (secure)")
            else:
                print("⚠️  WARNING: .env is NOT in .gitignore!")
                print("   Add '.env' to your .gitignore file to keep secrets safe")
        
        print("\n🎯 Environment setup complete!")
        print("📁 Files created:")
        print("   - .env (with your actual API keys)")
        print("   - .env.example (template for others)")
        print("\n🚀 Your application can now use environment variables!")
        print("   Backend will load Supabase keys from .env")
        print("   Config.yaml will load Tavily API key from .env")
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        print("You may need to create it manually with the provided content")

if __name__ == "__main__":
    print("🔧 Setting up environment variables for Make It Heavy...")
    print("=" * 55)
    create_env_file()