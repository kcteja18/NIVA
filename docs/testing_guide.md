# NIVA Testing & Evaluation Guide

This document provides comprehensive test scenarios demonstrating successful, failed, and edge-case interactions.

---

## 1. Test Environment Setup

### Prerequisites
```bash
# 1. Ensure models are initialized
Click "Initialize Models" in UI (takes ~30 seconds)

# 2. Test microphone
Record a 3-second test → Verify waveform appears

# 3. Verify API key
Check .env file has valid GROQ_API_KEY
```

---

## 2. Successful Interactions (Happy Path)

### 2.1 Telugu - Scheme Search

**Scenario**: User asks about farmer schemes in Telugu

```
USER (Voice): "రైతు యోజనల గురించి చెప్పండి"

[Whisper STT] → "రైతు యోజనల గురించి చెప్పండి"
[Language Detection] → Telugu (te)

[Agent Thinking]
├─ Intent: User wants farmer-related schemes
├─ Action: Call search_schemes("రైతు", "te")
└─ Tool Response: Found PM Kisan scheme

AGENT (Voice): "నేను 1 యోజనను కనుగొన్నాను:

1. **ప్రధాన మంత్రి కిసాన్ సమ్మాన్ నిధి**
   వివరణ: రైతులకు సంవత్సరానికి 6000 రూపాయలు ఆర్థిక సహాయం మూడు విడతల్లో అందించబడుతుంది.
   లాభాలు: సంవత్సరానికి 6000 రూపాయలు
   అవసరమైన పత్రాలు: ఆధార్ కార్డ్, బ్యాంక్ ఖాతా, భూమి రికార్డులు

మరింత సమాచారం కావాలా?"
```

**Expected Result**: ✅ PASS
- Correct Telugu transcription
- Relevant scheme found
- Response in Telugu
- Audio output in Telugu voice

---

### 2.2 English - Eligibility Check

**Scenario**: User provides details and checks eligibility

```
USER (Voice): "I am 35 years old, farmer, annual income 1.5 lakh. Am I eligible for PM Kisan?"

[Whisper STT] → Transcribed correctly
[Language Detection] → English (en)

[Agent Thinking]
├─ Intent: Check eligibility for PM Kisan
├─ Extracted: age=35, income=150000, occupation=farmer
├─ Action: Call check_eligibility("PM Kisan", 35, 150000, "farmer", None, "en")
└─ Tool Response: Eligible ✅

AGENT (Voice): "✅ Congratulations! You are eligible for **PM Kisan Samman Nidhi**!

Benefits: ₹6000 per year
Required documents: Aadhar Card, Bank Account, Land Records

Visit your nearest CSC center or government office to apply."
```

**Expected Result**: ✅ PASS
- Correct English transcription
- Eligibility correctly evaluated
- Response in English
- Audio output in English voice

---

### 2.3 Bilingual - All Schemes List

**Scenario**: User wants to see all available schemes (Telugu)

```
USER (Text): "అన్ని యోజనలు చూపించండి"

[Language Detection] → Telugu (te)

[Agent Thinking]
├─ Intent: List all schemes
├─ Action: Call get_all_schemes("te")
└─ Tool Response: All 6 schemes

AGENT: "అందుబాటులో ఉన్న ప్రభుత్వ యోజనలు:

1. **ప్రధాన మంత్రి కిసాన్ సమ్మాన్ నిధి** (agriculture)
2. **ప్రధాన మంత్రి ఆవాస్ యోజన** (housing)
3. **ఆయుష్మాన్ భారత్ యోజన** (health)
4. **ప్రధాన మంత్రి జన్ ధన్ యోజన** (finance)
5. **ప్రధాన మంత్రి సురక్ష బీమా యోజన** (insurance)
6. **ప్రధాన మంత్రి ఉజ్జ్వల యోజన** (energy)

ఏదైనా యోజన యొక్క పూర్తి సమాచారం కోసం దాని పేరు చెప్పండి."
```

**Expected Result**: ✅ PASS
- All 6 schemes listed
- Telugu language maintained
- Proper formatting

---

## 3. Failed Interactions & Recovery

### 3.1 Unclear Audio Input

**Scenario**: User speaks unclearly or background noise

```
USER (Voice): [Mumbled/unclear audio with noise]

[Whisper STT] → "" (empty string)

AGENT: "❌ Could not understand audio. Please try again."

[UI shows error message in both languages]
```

**Expected Result**: ✅ RECOVERED
- Graceful error message
- User can retry
- No system crash

---

### 3.2 Incomplete User Information

**Scenario**: User asks eligibility without providing details

```
USER (Voice): "Am I eligible for PM Kisan?"

[Agent Thinking]
├─ Intent: Check eligibility
├─ Missing: age, income, occupation
└─ Action: Ask for required information

AGENT: "To check your eligibility for PM Kisan, I need some information:
1. What is your age?
2. What is your annual income?
3. Are you a farmer?

Please provide these details."
```

**Expected Result**: ✅ RECOVERED
- Agent identifies missing information
- Politely asks specific questions
- Maintains context for follow-up

---

### 3.3 Scheme Not Found

**Scenario**: User asks about non-existent scheme

```
USER (Telugu): "జాతీయ పెన్షన్ యోజన గురించి చెప్పండి"

[Agent Thinking]
├─ Intent: Get scheme details
├─ Action: Call search_schemes("జాతీయ పెన్షన్", "te")
└─ Tool Response: No matches

AGENT: "కోరిన యోజనలు కనబడలేదు. దయచేసి వేరే పదాలతో వెతకండి.

నేను ఈ రకమైన యోజనలలో సహాయం చేయగలను:
- రైతు యోజనలు (PM Kisan)
- గృహనిర్మాణ యోజనలు (PM Awas)
- ఆరోగ్య యోజనలు (Ayushman Bharat)

మీరు ఏది గురించి తెలుసుకోవాలనుకుంటున్నారు?"
```

**Expected Result**: ✅ RECOVERED
- Graceful "not found" message
- Suggests available alternatives
- Maintains conversation flow

---

## 4. Edge Cases

### 4.1 Language Switching Mid-Conversation

**Scenario**: User switches from Telugu to English

```
Turn 1:
USER: "రైతు యోజనలు చెప్పండి"
AGENT: [Telugu response about PM Kisan]

Turn 2:
USER: "What are the documents needed?"
[Language Detection] → English (en)

AGENT: "For PM Kisan, the required documents are:
• Aadhar Card
• Bank Account
• Land Records

Would you like help with the application process?"
```

**Expected Result**: ✅ SUCCESS
- Agent detects language change
- Switches response language
- Maintains topic context

---

### 4.2 Contradictory Information

**Scenario**: User provides conflicting information

```
Turn 1:
USER (English): "My annual income is 10 lakh rupees"
AGENT: "Noted. Your income is ₹10,00,000."

Turn 2:
USER: "I want to apply for Ayushman Bharat as I am from BPL family"

[Agent Thinking]
├─ Previous info: income = 10,00,000
├─ New claim: BPL (should be < 2,50,000)
└─ Contradiction detected!

AGENT: "I need some clarification. You mentioned earlier that your annual income is ₹10 lakh, but BPL (Below Poverty Line) families typically have income under ₹2.5 lakh.

Could you please confirm your correct annual income? This will help me check your eligibility accurately."
```

**Expected Result**: ✅ SUCCESS
- Agent detects contradiction
- Points it out politely
- Asks for clarification
- Maintains conversation history

---

### 4.3 Mixed Language Input (Hinglish-style)

**Scenario**: User mixes Telugu and English words

```
USER: "Farmer schemes gurinchi cheppandi"
[Telugu script: "ఫార్మర్ schemes గురించి చెప్పండి"]

[Whisper STT] → May transcribe as mixed
[Language Detection] → Telugu (due to Telugu script)

[Agent Thinking]
├─ Detected: Telugu (te)
├─ Keywords: "farmer", "schemes", "గురించి"
├─ Action: Call search_schemes("farmer", "te")
└─ Response in Telugu

AGENT: "నేను రైతు యోజనలను కనుగొన్నాను:

1. **ప్రధాన మంత్రి కిసాన్ సమ్మాన్ నిధి**
   వివరణ: రైతులకు సంవత్సరానికి 6000 రూపాయలు..."
```

**Expected Result**: ✅ SUCCESS
- Handles mixed input
- Responds in detected primary language
- Finds relevant schemes

---

### 4.4 Multi-Turn Conversation with Context

**Scenario**: User asks follow-up questions

```
Turn 1:
USER: "Tell me about health schemes"
AGENT: [Lists Ayushman Bharat with details]

Turn 2:
USER: "What is the income limit?"
[Agent remembers context: health schemes → Ayushman Bharat]

AGENT: "For Ayushman Bharat, the maximum annual income limit is ₹2,50,000. 

The scheme is designed for Below Poverty Line (BPL) families to provide health insurance coverage up to ₹5 lakh."

Turn 3:
USER: "And what documents?"
[Agent still in context]

AGENT: "For Ayushman Bharat, you need:
• Aadhar Card
• Ration Card
• BPL Certificate

You can apply at your nearest CSC center."
```

**Expected Result**: ✅ SUCCESS
- Memory maintained across 3 turns
- No need to repeat scheme name
- Context-aware responses

---

### 4.5 Negative Eligibility Check

**Scenario**: User is not eligible

```
USER: "I am 40 years old, income 5 lakh. Am I eligible for Ayushman Bharat?"

[Agent Thinking]
├─ Intent: Check eligibility
├─ Extracted: age=40, income=500000
├─ Action: Call check_eligibility("Ayushman", 40, 500000, None, None, "en")
├─ Eligibility Check:
│   • Age: ✅ (no restriction)
│   • Income: ❌ (> 2,50,000 limit)
│   • Category: ❌ (Not BPL)
└─ Result: Not eligible

AGENT: "❌ You are not eligible for **Ayushman Bharat Yojana**.

Reasons:
• Income exceeds limit (₹2,50,000)
• Your category should be one of (BPL)

Would you like me to suggest other schemes that might suit your profile?"
```

**Expected Result**: ✅ SUCCESS
- Clear ineligibility explanation
- Specific reasons provided
- Offers alternative help

---

## 5. Performance Testing

### 5.1 Latency Benchmarks

| Component | Expected Time |
|-----------|---------------|
| STT (5 sec audio) | 2-3 seconds |
| Agent processing | 1-2 seconds |
| TTS synthesis | 1-2 seconds |
| **Total** | **4-7 seconds** |

### 5.2 Load Testing

```
Scenario: 10 consecutive queries
Expected: All succeed within 10 seconds each
Memory: Should stay under 3GB RAM
```

---

## 6. Test Checklist

### ✅ Voice Input Tests
- [ ] Clear Telugu audio → Correct transcription
- [ ] Clear English audio → Correct transcription
- [ ] Noisy audio → Error handling
- [ ] Silent audio → Error handling

### ✅ Agent Tests
- [ ] Scheme search (Telugu) → Finds schemes
- [ ] Scheme search (English) → Finds schemes
- [ ] Eligibility check (eligible) → Correct result
- [ ] Eligibility check (not eligible) → Correct result
- [ ] All schemes list → Returns all 6 schemes
- [ ] Unknown scheme → Graceful error

### ✅ Conversation Tests
- [ ] Single turn → Responds correctly
- [ ] Multi-turn (3+) → Maintains context
- [ ] Language switch → Adapts language
- [ ] Contradiction → Detects and asks

### ✅ Error Handling Tests
- [ ] No microphone → Falls back to text
- [ ] Invalid API key → Shows error
- [ ] Network error → Retry/error message
- [ ] Incomplete info → Asks questions

---

## 7. Demo Video Script

**Total Duration**: 5-7 minutes

### Minute 1: Introduction
- Project name and objective
- Tech stack overview
- Show architecture diagram

### Minutes 2-3: Happy Path Demo
- Telugu voice input: "రైతు యోజనలు చెప్పండి"
- Show STT transcription
- Show agent thinking (verbose mode)
- Show TTS output
- Play audio response

### Minute 4: Eligibility Check
- English voice: "I am 35, farmer, income 1.5 lakh"
- Show eligibility evaluation
- Show tool calling
- Demonstrate positive result

### Minute 5: Failure Recovery
- Show unclear audio → error recovery
- Show incomplete info → agent asks questions
- Show invalid scheme → graceful handling

### Minutes 6-7: Edge Cases
- Language switching
- Multi-turn conversation
- Contradiction detection
- Wrap-up and conclusion

---

## 8. Automated Test Script

```python
# test_niva.py
import sys
sys.path.insert(0, 'src')

from src.agent import SchemeAgent

def test_agent():
    agent = SchemeAgent()
    
    # Test 1: Telugu search
    result = agent.process("రైతు యోజనలు చెప్పండి")
    assert result['language'] == 'te'
    assert 'కిసాన్' in result['response']
    print("✅ Test 1 passed")
    
    # Test 2: English eligibility
    result = agent.process("I am 35, farmer, income 150000. Check PM Kisan eligibility")
    assert result['language'] == 'en'
    assert 'eligible' in result['response'].lower()
    print("✅ Test 2 passed")
    
    # Test 3: All schemes
    result = agent.process("Show all schemes")
    assert '6' in result['response'] or 'six' in result['response'].lower()
    print("✅ Test 3 passed")
    
    print("\n🎉 All tests passed!")

if __name__ == "__main__":
    test_agent()
```

---

**All test scenarios documented and ready for evaluation!**
