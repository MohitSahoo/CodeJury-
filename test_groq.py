"""Test Groq API connectivity."""

import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("❌ GROQ_API_KEY not found in .env")
    exit(1)

print(f"Testing Groq API with key: {api_key[:20]}...")

client = Groq(api_key=api_key)

try:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=10,
    )

    print("\n✅ Groq API works!")
    print(f"Response: {response.choices[0].message.content}")
    print(f"Tokens used: {response.usage.total_tokens}")

except Exception as e:
    print(f"\n❌ Groq API failed:")
    print(f"Error: {e}")
