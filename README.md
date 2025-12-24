# NIVA - Voice-Based Government Scheme Assistant  
### నివా - వాయిస్-బేస్డ్ ప్రభుత్వ యోజనా సహాయకుడు

A voice-first, agentic AI system that helps users discover and apply for government welfare schemes in **Telugu** and **English**.

---

## 🎯 Features

- ✅ **Voice-First Interaction**: Complete STT → LLM → TTS pipeline
- ✅ **Bilingual Support**: Telugu (తెలుగు) + English with automatic language detection
- ✅ **Agentic Reasoning**: LangGraph StateGraph with Planner-Executor-Synthesizer nodes
- ✅ **7 Smart Tools**: Vector search, eligibility, comparison, benefits, application steps
- ✅ **Conversation Memory**: AgentState with user context tracking
- ✅ **ChromaDB Vector Store**: Semantic search with all-MiniLM-L6-v2 embeddings
- ✅ **Failure Handling**: Graceful error recovery and clarification requests
- ✅ **100% Free Stack**: No paid APIs required

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GRADIO UI                                │
│  🎤 Voice Input  │  ⌨️ Text Input  │  🔊 Audio Output      │
└────────┬─────────────────┬────────────────────┬────────────┘
         │                 │                    │
         ▼                 │                    ▲
┌─────────────────┐        │         ┌──────────────────┐
│  Groq Whisper   │        │         │   Edge-TTS       │
│  (whisper-      │        │         │ (Telugu/English) │
│  large-v3)      │        │         └──────────────────┘
└────────┬────────┘        │                    │
         │                 │                    │
         └────────┬────────┘                    │
                  ▼                             │
      ┌───────────────────────────┐             │
      │   LangGraph Agent         │             │
      │   ┌─────────────────┐     │             │
      │   │ Groq LLM        │     │             │
      │   │ (Llama 3.3 70B) │     │             │
      │   └─────────────────┘     │             │
      │                           │             │
      │   ┌─────────────────┐     │             │
      │   │ StateGraph:     │     │─────────────┘
      │   │ planner→executor│     │
      │   │ →synthesizer    │     │
      │   └─────────────────┘     │
      │                           │
      │   ┌─────────────────┐     │
      │   │ 7 Tools:        │     │
      │   │ • vector_search │     │
      │   │ • eligibility   │     │
      │   │ • compare, etc. │     │
      │   └─────────────────┘     │
      └───────────┬───────────────┘
                  │
                  ▼
      ┌───────────────────────────┐
      │  ChromaDB + schemes.json  │
      │  Vector store + 6 schemes │
      └───────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- Microphone (for voice input)
- Internet connection (for Groq API and TTS)

### 2. Installation

```bash
# Clone repository
git clone https://github.com/kcteja18/NIVA.git
cd NIVA

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Get FREE Groq API Key

1. Visit: https://console.groq.com/keys
2. Sign up (no credit card required)
3. Click "Create API Key"
4. Copy your API key

### 4. Configure Environment

```bash
# Create .env file
cp .env.example .env

# Edit .env and add your Groq API key
GROQ_API_KEY=your_api_key_here
```

### 5. Run the Application

```bash
python app.py
```

The app will open at: **http://localhost:7860**

---

## 📖 Usage Guide

### Voice Interaction

1. Click **"Initialize Models"** (one-time setup)
2. Go to **"Voice Input"** tab
3. Click **🎤** and speak your question (Telugu or English)
4. Click **"Process Voice"**
5. Listen to the response!

### Text Interaction

1. Go to **"Text Input"** tab
2. Type your question in Telugu or English
3. Click **"Send"**
4. Read and listen to the response

### Example Queries

**Telugu (తెలుగు):**
```
- రైతు యోజనలు చెప్పండి
- నా వయస్సు 35, ఆదాయం 1.5 లక్షలు. నేను రైతును. నేను PM Kisan కు అర్హుడినా?
- అన్ని యోజనలు చూపించండి
- ఆయుష్మాన్ భారత్ గురించి చెప్పండి
```

**English:**
```
- Tell me about farmer schemes
- I am 35 years old, income 1.5 lakh. Am I eligible for PM Kisan?
- Show all schemes
- Tell me about Ayushman Bharat
```

---

## 🛠️ Tech Stack

| Component | Technology | Why | Cost |
|-----------|------------|-----|------|
| **STT** | Groq Whisper API (whisper-large-v3) | Fast cloud-based transcription | FREE |
| **LLM** | Groq (llama-3.3-70b-versatile) | 500+ tokens/sec, excellent multilingual | FREE (14.4K requests/day) |
| **TTS** | Edge-TTS | Natural Microsoft neural voices | FREE |
| **Agent** | LangGraph | StateGraph with conditional routing | FREE |
| **Vector DB** | ChromaDB | Semantic search with embeddings | FREE |
| **UI** | Gradio | Quick prototyping, audio support | FREE |
| **Database** | JSON | Simple, sufficient for demo | FREE |

**Total Cost: $0.00** ✅

---

## 📊 Government Schemes Database

The system includes 6 major schemes with bilingual data:

1. **PM Kisan Samman Nidhi** (ప్రధాన మంత్రి కిసాన్ సమ్మాన్ నిధి) - Agriculture
2. **PM Awas Yojana** (ప్రధాన మంత్రి ఆవాస్ యోజన) - Housing
3. **Ayushman Bharat** (ఆయుష్మాన్ భారత్) - Health
4. **PM Jan Dhan Yojana** (ప్రధాన మంత్రి జన్ ధన్ యోజన) - Finance
5. **PM Suraksha Bima** (ప్రధాన మంత్రి సురక్ష బీమా) - Insurance
6. **PM Ujjwala Yojana** (ప్రధాన మంత్రి ఉజ్జ్వల యోజన) - Energy

---

## 🧪 Testing

Test different scenarios:

### ✅ Happy Path
```
User: "రైతు యోజనలు చెప్పండి"
Agent: [Lists PM Kisan with details]
```

### ✅ Eligibility Check
```
User: "I am 35 years old, farmer, income 1.5 lakh"
Agent: [Checks eligibility and provides result]
```

### ✅ Incomplete Information
```
User: "Am I eligible?"
Agent: "Please provide: age, income, occupation"
```

### ✅ Error Recovery
```
User: [Unclear audio]
Agent: "Could not understand. Please try again"
```

---

## 📁 Project Structure

```
NIVA/
├── app.py                     # Gradio UI (main entry point)
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── README.md                 # This file
├── test_niva.py              # Automated test suite
│
├── src/
│   ├── __init__.py           # Package init
│   ├── groq_stt.py           # Groq Whisper STT module
│   ├── tts.py                # Edge-TTS module
│   ├── langgraph_agent.py    # LangGraph agent with StateGraph
│   ├── tools.py              # 7 LangChain tools
│   └── vector_store.py       # ChromaDB vector store
│
├── data/
│   └── schemes.json          # Bilingual schemes database
│
├── chroma_db/                # ChromaDB persistent storage
│
└── docs/
    ├── architecture.md       # Technical architecture
    ├── evaluation_transcript.md  # Test interactions
    └── PROJECT_SUMMARY.md    # Project summary
```

---

