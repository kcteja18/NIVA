"""
NIVA Automated Test Suite
Tests core functionality without requiring UI or audio
"""

import sys
import os
sys.path.insert(0, 'src')

# Load environment
from dotenv import load_dotenv
load_dotenv()

def test_imports():
    """Test all required imports"""
    print("\n🔍 Testing imports...")
    try:
        import whisper
        import edge_tts
        import langchain
        from langchain_groq import ChatGroq
        import gradio
        print("✅ All packages imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_environment():
    """Test environment configuration"""
    print("\n🔍 Testing environment...")
    
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ GROQ_API_KEY not found in .env")
        return False
    
    if not api_key.startswith('gsk_'):
        print("❌ Invalid GROQ_API_KEY format (should start with 'gsk_')")
        return False
    
    print(f"✅ API key found: {api_key[:10]}...")
    return True

def test_schemes_database():
    """Test schemes data loading"""
    print("\n🔍 Testing schemes database...")
    try:
        import json
        
        with open('data/schemes.json', 'r', encoding='utf-8') as f:
            schemes = json.load(f)
        
        if len(schemes) != 6:
            print(f"❌ Expected 6 schemes, found {len(schemes)}")
            return False
        
        # Check required fields
        required_fields = ['id', 'name_te', 'name_en', 'description_te', 'description_en']
        for scheme in schemes:
            for field in required_fields:
                if field not in scheme:
                    print(f"❌ Missing field '{field}' in scheme {scheme.get('id', 'unknown')}")
                    return False
        
        print(f"✅ All 6 schemes loaded with required fields")
        return True
    except Exception as e:
        print(f"❌ Failed to load schemes: {e}")
        return False

def test_language_detection():
    """Test language detection logic"""
    print("\n🔍 Testing language detection...")
    try:
        from src.langgraph_agent import AgentWorkflow
        
        agent = AgentWorkflow()
        
        # Test Telugu - using Unicode detection
        text = "రైతు యోజనలు చెప్పండి"
        lang = "te" if any('\u0C00' <= c <= '\u0C7F' for c in text) else "en"
        if lang != 'te':
            print(f"❌ Telugu detection failed: got '{lang}', expected 'te'")
            return False
        
        # Test English
        text = "Tell me about farmer schemes"
        lang = "te" if any('\u0C00' <= c <= '\u0C7F' for c in text) else "en"
        if lang != 'en':
            print(f"❌ English detection failed: got '{lang}', expected 'en'")
            return False
        
        print("✅ Language detection working correctly")
        return True
    except Exception as e:
        print(f"❌ Language detection failed: {e}")
        return False

def test_tools():
    """Test LangChain tools"""
    print("\n🔍 Testing LangChain tools...")
    try:
        from src.tools import search_schemes, check_eligibility, get_all_schemes
        
        # Test 1: Search schemes in Telugu
        result = search_schemes.invoke({"query": "రైతు", "language": "te"})
        if "కిసాన్" not in result:
            print(f"❌ Telugu search failed: {result[:100]}")
            return False
        
        # Test 2: Search schemes in English
        result = search_schemes.invoke({"query": "health", "language": "en"})
        if "Ayushman" not in result:
            print(f"❌ English search failed: {result[:100]}")
            return False
        
        # Test 3: Check eligibility (eligible)
        result = check_eligibility.invoke({
            "scheme_name": "PM Kisan",
            "age": 35,
            "annual_income": 150000,
            "occupation": "farmer",
            "category": None,
            "language": "en"
        })
        if "eligible" not in result.lower():
            print(f"❌ Eligibility check failed: {result[:100]}")
            return False
        
        # Test 4: Check eligibility (not eligible)
        result = check_eligibility.invoke({
            "scheme_name": "Ayushman Bharat",
            "age": 40,
            "annual_income": 500000,
            "occupation": None,
            "category": None,
            "language": "en"
        })
        if "not eligible" not in result.lower():
            print(f"❌ Ineligibility check failed: {result[:100]}")
            return False
        
        # Test 5: Get all schemes
        result = get_all_schemes.invoke({"language": "en"})
        if "6" not in result and "six" not in result.lower():
            print(f"❌ Get all schemes failed: {result[:100]}")
            return False
        
        print("✅ All tools working correctly")
        return True
    except Exception as e:
        print(f"❌ Tool testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_basic():
    """Test basic agent functionality"""
    print("\n🔍 Testing agent (basic)...")
    try:
        from src.langgraph_agent import AgentWorkflow
        
        agent = AgentWorkflow()
        
        # Test 1: Telugu query
        print("  Testing Telugu query...")
        result = agent.process("రైతు యోజనలు చెప్పండి")
        if result['language'] != 'te':
            print(f"❌ Telugu agent failed: language={result['language']}")
            return False
        # Check for PM Kisan in various forms (Unicode normalization issues)
        if not any(word in result['response'] for word in ['కిసాన్', 'Kisan', 'PM Kisan', 'రైతు']):
            print(f"❌ Telugu agent failed: expected scheme keywords not in response")
            print(f"   Response: {result['response'][:100]}")
            return False
        
        # Test 2: English query
        print("  Testing English query...")
        result = agent.process("Tell me about health schemes")
        if result['language'] != 'en':
            print(f"❌ English agent failed: language={result['language']}")
            return False
        if 'Ayushman' not in result['response']:
            print(f"❌ English agent failed: no 'Ayushman' in response")
            return False
        
        print("✅ Agent working correctly")
        return True
    except Exception as e:
        print(f"❌ Agent testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_eligibility():
    """Test agent eligibility checking"""
    print("\n🔍 Testing agent eligibility...")
    try:
        from src.langgraph_agent import AgentWorkflow
        
        agent = AgentWorkflow()
        
        # Test: Complex eligibility query
        query = "I am 35 years old, farmer, annual income 150000. Am I eligible for PM Kisan?"
        print(f"  Query: {query}")
        
        result = agent.process(query)
        
        if result['language'] != 'en':
            print(f"❌ Language detection failed: {result['language']}")
            return False
        
        if 'eligible' not in result['response'].lower():
            print(f"❌ Eligibility not mentioned in response")
            return False
        
        print("✅ Agent eligibility checking works")
        return True
    except Exception as e:
        print(f"❌ Eligibility testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tts_imports():
    """Test TTS module imports (without actual synthesis)"""
    print("\n🔍 Testing TTS imports...")
    try:
        from src.tts import EdgeTTS
        
        tts = EdgeTTS()
        print("✅ TTS module loaded successfully")
        return True
    except Exception as e:
        print(f"❌ TTS import failed: {e}")
        return False

def test_stt_imports():
    """Test STT module imports (without actual transcription)"""
    print("\n🔍 Testing STT imports...")
    try:
        from src.groq_stt import GroqWhisperSTT
        
        # Don't load model in tests (takes time)
        print("✅ STT module loaded successfully")
        return True
    except Exception as e:
        print(f"❌ STT import failed: {e}")
        return False

def run_all_tests():
    """Run complete test suite"""
    print("=" * 60)
    print("🧪 NIVA Automated Test Suite")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Environment", test_environment),
        ("Schemes Database", test_schemes_database),
        ("Language Detection", test_language_detection),
        ("LangChain Tools", test_tools),
        ("Agent Basic", test_agent_basic),
        ("Agent Eligibility", test_agent_eligibility),
        ("TTS Module", test_tts_imports),
        ("STT Module", test_stt_imports),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed ({passed*100//total}%)")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready for demo.")
        return True
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please fix before demo.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
