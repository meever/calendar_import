"""Test script to verify Gemini API key and extraction"""

import os
from dotenv import load_dotenv
from google import genai

# Load environment
load_dotenv()

# Get API key
api_key = os.getenv('GEMINI_API_KEY')
print(f"API Key loaded: {api_key[:20]}..." if api_key else "API Key: None")

# Configure and test
try:
    client = genai.Client(api_key=api_key)
    
    # List available models
    print("\nAvailable models:")
    models = client.models.list()
    for model in models:
        # New API returns model objects with name attribute
        print(f"  - {model.name}")
    
    # Test with a simple prompt
    print("\nTesting gemini-2.5-flash...")
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents="Say 'API working' in 2 words"
    )
    print(f"Response: {response.text}")
    print("\n✅ API key is valid and working!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
