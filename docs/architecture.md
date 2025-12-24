# NIVA Architecture Document

## 1. System Overview

NIVA (Native Indian Voice Assistant) is a voice-first, agentic AI system for government welfare scheme discovery in Telugu and English.

### Design Principles

1. **Voice-First**: Primary interaction via speech (STT → Agent → TTS)
2. **Bilingual**: Seamless Telugu ↔ English support
3. **Agentic**: LangGraph-based autonomous reasoning with tool usage
4. **Memory-Aware**: Multi-turn context maintenance with user parameter tracking
5. **Semantic Search**: ChromaDB vector store for intelligent scheme matching

---

## 2. High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│                            (Gradio Dark Theme)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ 🎤 Voice     │  │ ⌨️ Text      │  │ 💬 Chat      │  │ 🔊 Audio     │   │
│  │   Input      │  │   Input      │  │   Display    │  │   Output     │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘  └──────────────┘   │
└─────────┼─────────────────┼─────────────────────────────────────────────────┘
          │                 │
          ▼                 │
┌─────────────────────┐     │
│   GROQ WHISPER STT  │     │
│  ┌───────────────┐  │     │
│  │ whisper-large │  │     │
│  │ -v3 (API)     │  │     │
│  ├───────────────┤  │     │
│  │ Telugu Local  │  │     │
│  │ Fallback      │  │     │
│  └───────────────┘  │     │
└─────────┬───────────┘     │
          │                 │
          │ Transcribed     │
          │ Text            │
          └────────┬────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LANGGRAPH AGENT WORKFLOW                             │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         AGENT STATE (TypedDict)                        │ │
│  │  • user_input      • language           • conversation_history        │ │
│  │  • intent          • requires_info      • missing_info                │ │
│  │  • extracted_params • tool_to_use       • tool_results                │ │
│  │  • final_response                                                      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────────┐ │
│  │   PLANNER   │────▶│  EXECUTOR   │────▶│ SYNTHESIZER │────▶│   END    │ │
│  │             │     │             │     │             │     │          │ │
│  │ • Intent    │     │ • Tool Call │     │ • LLM       │     │          │ │
│  │ • Params    │     │ • Vector    │     │   Response  │     │          │ │
│  │ • Route     │     │   Search    │     │ • Format    │     │          │ │
│  └──────┬──────┘     └─────────────┘     └─────────────┘     └──────────┘ │
│         │                                                                   │
│         │ requires_info=True                                               │
│         ▼                                                                   │
│  ┌─────────────┐                                                           │
│  │  ASK_INFO   │──────────────────────────────────────────────▶ END       │
│  │             │                                                           │
│  │ • Missing   │                                                           │
│  │   Params    │                                                           │
│  │ • Questions │                                                           │
│  └─────────────┘                                                           │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    GROQ LLM (Llama 3.3 70B Versatile)                  │ │
│  │  • Temperature: 0.3        • Max Tokens: 1024                          │ │
│  │  • Free Tier: 14,400 req/day                                           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      CONVERSATION MEMORY                               │ │
│  │  • Rolling window: Last 10 messages (5 user + 5 assistant)            │ │
│  │  • User context: Persisted params (age, income, occupation)           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TOOLS (7 Total)                                 │
│                                                                              │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐               │
│  │ vector_search   │ │check_eligibility│ │ get_all_schemes │               │
│  │ (ChromaDB)      │ │                 │ │                 │               │
│  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘               │
│           │                   │                   │                         │
│  ┌────────┴────────┐ ┌────────┴────────┐ ┌───────┴─────────┐               │
│  │ compare_schemes │ │calculate_benefit│ │get_app_steps    │               │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘               │
│                              │                                              │
│  ┌───────────────────────────┴───────────────────────────┐                 │
│  │              get_schemes_by_sector                     │                 │
│  └────────────────────────────────────────────────────────┘                 │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                           │
│                                                                              │
│  ┌────────────────────────────────┐  ┌────────────────────────────────┐    │
│  │       ChromaDB Vector Store    │  │      schemes.json (6 schemes)  │    │
│  │  • PersistentClient            │  │                                │    │
│  │  • all-MiniLM-L6-v2 embeddings │  │  • PM Kisan (agriculture)      │    │
│  │  • Cosine similarity           │  │  • PM Awas (housing)           │    │
│  │  • Path: ./chroma_db           │  │  • Ayushman Bharat (health)    │    │
│  └────────────────────────────────┘  │  • PM Jan Dhan (finance)       │    │
│                                       │  • PM Suraksha (insurance)     │    │
│                                       │  • PM Ujjwala (energy)         │    │
│                                       └────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                               │
                               │ (Response flows back up)
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EDGE-TTS                                        │
│                                                                              │
│  Telugu Voices:                      English Voices:                        │
│  • Female: te-IN-ShrutiNeural        • Female: en-US-AriaNeural            │
│  • Male: te-IN-MohanNeural           • Male: en-US-GuyNeural               │
│                                                                              │
│  Features: Free (no API key) • Natural neural voices • MP3 output          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Agent Lifecycle

### 3.1 Complete Request Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENT LIFECYCLE                                    │
└─────────────────────────────────────────────────────────────────────────────┘

1. USER INPUT
   │
   ├── Voice: Gradio microphone → numpy array (48kHz)
   │           → Resample to 16kHz
   │           → Groq Whisper API → Text
   │
   └── Text: Direct input from textbox
   
2. LANGUAGE DETECTION
   │
   └── Unicode Range Check: '\u0C00' <= char <= '\u0C7F'
       │
       ├── Telugu characters found → lang = "te"
       └── No Telugu characters    → lang = "en"

3. STATE INITIALIZATION
   │
   └── AgentState = {
           user_input: "రైతు యోజనలు చెప్పండి",
           language: "te",
           conversation_history: [...],
           intent: "",
           requires_info: False,
           missing_info: [],
           extracted_params: {},
           tool_to_use: "",
           tool_results: "",
           final_response: ""
       }

4. GRAPH EXECUTION
   │
   ├── Entry Point: PLANNER
   │   │
   │   ├── Extract parameters (age, income, occupation, scheme)
   │   ├── Merge with user_context (persistent)
   │   ├── Detect intent (8 types)
   │   └── Select tool
   │
   ├── Conditional Routing
   │   │
   │   ├── requires_info=True  → ASK_INFO → END
   │   ├── intent="greet"      → SYNTHESIZER → END
   │   └── Otherwise           → EXECUTOR → SYNTHESIZER → END
   │
   ├── EXECUTOR (if routed)
   │   │
   │   └── Call selected tool with params
   │       • vector_search: ChromaDB semantic search
   │       • check_eligibility: Rule-based validation
   │       • get_all_schemes: Return all 6 schemes
   │       • etc.
   │
   └── SYNTHESIZER
       │
       └── LLM generates bilingual response
           • Telugu prompt: "మీరు NIVA. తెలుగులో..."
           • English prompt: "You are NIVA. Reply in English..."

5. RESPONSE HANDLING
   │
   ├── Add to conversation_history (max 10 messages)
   ├── Update user_context with extracted params
   └── Return {response, language, intent}

6. TTS SYNTHESIS
   │
   └── Edge-TTS → MP3 audio file
       • Language-appropriate voice selection
       • Async synthesis with asyncio
```

### 3.2 Node Functions

| Node | Function | Purpose |
|------|----------|---------|
| `_planner` | Intent + Parameter Extraction | Analyzes input, extracts age/income/occupation, detects intent |
| `_executor` | Tool Invocation | Calls appropriate tool based on intent |
| `_synthesizer` | Response Generation | LLM generates natural language response |
| `_ask_info` | Missing Info Handler | Asks user for required parameters |
| `_route` | Conditional Router | Decides next node based on state |

---

## 4. Decision Flow

### 4.1 Intent Classification

```python
INTENT_KEYWORDS = {
    "greet":       ['hello', 'hi', 'నమస్కారం', 'హలో'],
    "compare":     ['compare', 'vs', 'పోలిక'],
    "calculate":   ['how much', 'calculate', 'ఎంత'],
    "apply":       ['apply', 'process', 'దరఖాస్తు'],
    "eligibility": ['eligible', 'అర్హత', 'నాకు వస్తుందా'],
    "sector":      ['agriculture', 'health', 'housing', 'విభాగం'],
    "all":         ['all schemes', 'అన్ని యోజన', 'జాబితా'],
    "search":      [default - semantic vector search]
}
```

### 4.2 Tool Selection Matrix

| Intent | Tool | Description |
|--------|------|-------------|
| `search` | `vector_search` | ChromaDB semantic similarity |
| `eligibility` | `check_eligibility` | Rule-based validation |
| `compare` | `compare_schemes` | Side-by-side comparison |
| `calculate` | `calculate_benefits` | Benefit estimation |
| `apply` | `get_application_steps` | Step-by-step guide |
| `sector` | `get_schemes_by_sector` | Filter by sector |
| `all` | `get_all_schemes` | List all 6 schemes |
| `greet` | `none` | Direct greeting response |

### 4.3 Conditional Routing Logic

```
                    ┌─────────────┐
                    │   PLANNER   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
     requires_info    intent==greet   default
        = True                          
              │            │            │
              ▼            ▼            ▼
         ASK_INFO     SYNTHESIZER   EXECUTOR
              │            │            │
              ▼            │            ▼
             END           │       SYNTHESIZER
                           │            │
                           ▼            ▼
                          END          END
```

---

## 5. Memory Architecture

### 5.1 Conversation History

```python
# Rolling window - last 10 messages
conversation_history = [
    {"role": "user", "content": "రైతు యోజనలు చెప్పండి"},
    {"role": "assistant", "content": "PM కిసాన్..."},
    {"role": "user", "content": "దీనికి ఏ పత్రాలు కావాలి?"},
    {"role": "assistant", "content": "ఆధార్, బ్యాంక్ ఖాతా..."},
    # ... up to 10 messages
]

# Auto-trim when exceeds limit
if len(conversation_history) > 10:
    conversation_history = conversation_history[-10:]
```

### 5.2 User Context (Persistent Parameters)

```python
# Persists across turns within session
user_context = {
    "age": 35,
    "income": 150000,
    "occupation": "farmer",
    "scheme_name": "pm_kisan"
}

# Merge logic in _planner:
for k, v in self.user_context.items():
    if k not in extracted_params:
        extracted_params[k] = v  # Use cached value
self.user_context.update(extracted_params)  # Update cache
```

### 5.3 Memory Benefits

| Feature | Implementation |
|---------|----------------|
| **Multi-turn context** | Previous messages passed to LLM |
| **Parameter persistence** | Age, income, etc. remembered |
| **Follow-up handling** | "What documents?" refers to last scheme |
| **Session isolation** | `clear_history()` resets all state |

---

## 6. Prompts

### 6.1 Synthesizer Prompts

**Telugu Prompt:**
```
మీరు NIVA. తెలుగులో మాత్రమే 4-6 వాక్యాలలో సమాధానం ఇవ్వండి.
సమాచారం: {tool_results}
```

**English Prompt:**
```
You are NIVA. Reply in English only, 4-6 sentences.
Info: {tool_results}
```

### 6.2 Ask Info Prompts

**Telugu:**
```
🤔 కొంత సమాచారం అవసరం:
❓ ఏ యోజన కోసం?
❓ మీ వయస్సు?
```

**English:**
```
🤔 Need some info:
❓ Which scheme?
❓ Your age?
```

### 6.3 Greeting Responses

**Telugu:**
```
నమస్కారం! 🙏 నేను NIVA. ఏ యోజన గురించి తెలుసుకోవాలి?
```

**English:**
```
Hello! 🙏 I'm NIVA. Which scheme would you like to know about?
```

---

## 7. Component Details

### 7.1 Speech-to-Text (Groq Whisper)

| Property | Value |
|----------|-------|
| **Model** | whisper-large-v3 |
| **API** | Groq (free tier) |
| **Fallback** | vasista22/whisper-telugu-large-v2 (local) |
| **Sample Rate** | 16kHz (resampled from 48kHz) |
| **Languages** | Telugu (te), English (en) |

### 7.2 Vector Store (ChromaDB)

| Property | Value |
|----------|-------|
| **Client** | PersistentClient |
| **Path** | ./chroma_db |
| **Embeddings** | all-MiniLM-L6-v2 |
| **Distance** | Cosine similarity |
| **Documents** | 6 schemes (bilingual text) |

### 7.3 Text-to-Speech (Edge-TTS)

| Property | Value |
|----------|-------|
| **Technology** | Microsoft Edge Neural TTS |
| **Cost** | Free (no API key) |
| **Telugu Voice** | te-IN-ShrutiNeural |
| **English Voice** | en-US-AriaNeural |
| **Output** | MP3 |

---

## 8. Parameter Extraction

### 8.1 Regex Patterns

```python
# Age extraction
age_match = re.search(r'\b(\d{1,2})\s*(?:years|సంవత్సరాలు|వయస్సు|ఏళ్ళు)', text)

# Income extraction  
income_match = re.search(r'₹?\s*(\d+(?:,\d+)*)', text)

# Occupation detection
if any(w in lower for w in ['farmer', 'రైతు', 'agriculture']):
    params['occupation'] = 'farmer'
```

### 8.2 Scheme Name Mapping

```python
scheme_map = {
    'kisan': 'pm_kisan',
    'కిసాన్': 'pm_kisan',
    'awas': 'pm_awas',
    'ఆవాస్': 'pm_awas',
    'ayushman': 'ayushman_bharat',
    'ఆయుష్మాన్': 'ayushman_bharat',
    'jan dhan': 'pm_jan_dhan',
    'suraksha': 'pm_suraksha',
    'సురక్ష': 'pm_suraksha',
    'ujjwala': 'pm_ujjwala'
}
```

---

## 9. Performance Metrics

| Metric | Value |
|--------|-------|
| **STT Latency** | 1-3 seconds |
| **Agent Processing** | 1-2 seconds |
| **TTS Synthesis** | 0.5-2 seconds |
| **Total End-to-End** | 3-7 seconds |
| **Memory Usage** | ~1GB RAM |
| **ChromaDB Index** | ~5MB |

---

## 10. File Structure

```
NIVA/
├── app.py                      # Gradio UI (492 lines)
├── src/
│   ├── __init__.py            # Package exports
│   ├── langgraph_agent.py     # LangGraph workflow (223 lines)
│   ├── groq_stt.py            # Groq Whisper STT (100 lines)
│   ├── tts.py                 # Edge-TTS (93 lines)
│   ├── vector_store.py        # ChromaDB (101 lines)
│   └── tools.py               # 7 LangChain tools (490 lines)
├── data/
│   └── schemes.json           # 6 government schemes
├── chroma_db/                 # Persistent vector store
├── docs/
│   ├── architecture.md        # This document
│   ├── evaluation_transcript.md
│   └── testing_guide.md
├── test_niva.py               # Automated test suite
├── requirements.txt           # Dependencies
├── .env.example              # API key template
└── README.md                 # Setup instructions
```

---

## 11. Error Handling

### 11.1 STT Failures
- **Groq API error** → Fallback to local Telugu model
- **Empty transcription** → Return error message in UI
- **Sample rate mismatch** → Auto-resample to 16kHz

### 11.2 Agent Failures
- **Missing required params** → Route to ASK_INFO node
- **Tool execution error** → Graceful error message
- **LLM timeout** → Default error response

### 11.3 TTS Failures
- **Synthesis error** → Return text-only response
- **Invalid language** → Default to English voice

---

## 12. Security Considerations

- **API Keys**: Stored in `.env` file (not committed)
- **User Data**: No persistent storage of user info
- **Session Isolation**: Memory cleared between sessions

---

*Architecture designed for NIVA v1.0 - December 2024*
