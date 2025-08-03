"""
Configuration loader with environment variable support.
Loads config.yaml and expands ${VAR_NAME} placeholders with environment variables.
"""

import os
import yaml
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def expand_env_vars(data):
    """
    Recursively expand environment variables in a data structure.
    Replaces ${VAR_NAME} with the value of environment variable VAR_NAME.
    """
    if isinstance(data, dict):
        return {key: expand_env_vars(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [expand_env_vars(item) for item in data]
    elif isinstance(data, str):
        # Pattern to match ${VAR_NAME} or $VAR_NAME
        pattern = r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)'
        
        def replace_var(match):
            var_name = match.group(1) or match.group(2)
            return os.getenv(var_name, match.group(0))  # Return original if env var not found
        
        return re.sub(pattern, replace_var, data)
    else:
        return data

def load_config(config_path="config.yaml"):
    """
    Load configuration file with environment variable expansion.
    
    Args:
        config_path (str): Path to the YAML configuration file
        
    Returns:
        dict: Configuration dictionary with expanded environment variables
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Expand environment variables
        config = expand_env_vars(config)
        
        return config
        
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML configuration: {e}")
    except Exception as e:
        raise RuntimeError(f"Error loading configuration: {e}")

# Backwards compatibility - load config when module is imported
try:
    config = load_config()
except Exception as e:
    print(f"⚠️  Warning: Could not load config.yaml: {e}")
    config = {}

if __name__ == "__main__":
    # Test the configuration loader
    print("🧪 Testing configuration loader...")
    
    try:
        test_config = load_config()
        
        print("✅ Configuration loaded successfully!")
        print(f"📊 Sections found: {list(test_config.keys())}")
        
        # Test Tavily API key expansion
        tavily_key = test_config.get('tavily', {}).get('api_key', 'NOT_FOUND')
        if tavily_key.startswith('${') or tavily_key == 'NOT_FOUND':
            print(f"⚠️  Tavily API key: {tavily_key} (check your .env file)")
        else:
            print(f"✅ Tavily API key loaded: {tavily_key[:20]}...")
        
        # Test Ollama configuration
        ollama_url = test_config.get('ollama', {}).get('base_url', 'NOT_FOUND')
        print(f"🔌 Ollama URL: {ollama_url}")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")