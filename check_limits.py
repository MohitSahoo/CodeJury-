
import os
import google.generativeai as genai
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def test_gemini():
    print("Testing Gemini API...")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env")
        return False
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    try:
        response = model.generate_content("Say 'Gemini OK'")
        print(f"✅ Gemini API works: {response.text.strip()}")
        return True
    except Exception as e:
        print(f"❌ Gemini API failed: {e}")
        return False

def test_groq():
    print("\nTesting Groq API...")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY not found in .env")
        return False
    
    client = Groq(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say 'Groq OK'"}],
            max_tokens=10,
        )
        print(f"✅ Groq API works: {response.choices[0].message.content.strip()}")
        return True
    except Exception as e:
        print(f"❌ Groq API failed: {e}")
        return False

if __name__ == "__main__":
    gemini_ok = test_gemini()
    groq_ok = test_groq()
    
    if gemini_ok and groq_ok:
        print("\n✨ Both API keys are working correctly!")
    else:
        print("\n⚠️ One or more API keys hit a limit or failed.")
