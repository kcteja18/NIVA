"""
LangGraph-based Agentic Workflow for Government Schemes.

Architecture:
- Planner: Intent detection + parameter extraction
- Executor: ChromaDB search + eligibility tools  
- Synthesizer: LLM response generation
- Conditional routing for missing info
"""
import os
import re
from typing import TypedDict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from .tools import check_eligibility, get_all_schemes, compare_schemes, calculate_benefits, get_application_steps, get_schemes_by_sector
from .vector_store import get_vector_store

load_dotenv()


class AgentState(TypedDict):
    user_input: str
    language: str
    conversation_history: list
    intent: str
    requires_info: bool
    missing_info: list
    extracted_params: dict
    tool_to_use: str
    tool_results: str
    final_response: str


class AgentWorkflow:
    """LangGraph agent with conditional routing."""
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found")
        
        self.llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=api_key, temperature=0.3, max_tokens=1024)
        self.vector_store = get_vector_store()
        self.graph = self._build_graph()
        self.current_language = "te"
        self.conversation_history = []
        self.user_context = {}
        print("✅ LangGraph Agent initialized!")
    
    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("planner", self._planner)
        workflow.add_node("executor", self._executor)
        workflow.add_node("synthesizer", self._synthesizer)
        workflow.add_node("ask_info", self._ask_info)
        
        workflow.add_conditional_edges("planner", self._route, {"ask_info": "ask_info", "executor": "executor", "synthesizer": "synthesizer"})
        workflow.add_edge("executor", "synthesizer")
        workflow.add_edge("ask_info", END)
        workflow.add_edge("synthesizer", END)
        workflow.set_entry_point("planner")
        return workflow.compile()
    
    def _route(self, state: AgentState) -> str:
        if state["requires_info"] and state["missing_info"]:
            return "ask_info"
        return "synthesizer" if state["intent"] == "greet" else "executor"
    
    def _extract_params(self, text: str) -> dict:
        params = {}
        lower = text.lower()
        
        # Age
        age_match = re.search(r'\b(\d{1,2})\s*(?:years|సంవత్సరాలు|వయస్సు|ఏళ్ళు)', text, re.IGNORECASE)
        if age_match:
            params['age'] = int(age_match.group(1))
        elif re.search(r'\b(\d{2})\b', text):
            age = int(re.search(r'\b(\d{2})\b', text).group(1))
            if 18 <= age <= 80:
                params['age'] = age
        
        # Income
        income_match = re.search(r'₹?\s*(\d+(?:,\d+)*)', text)
        if income_match:
            income = int(income_match.group(1).replace(',', ''))
            params['income'] = income * 100000 if income < 100 else income
        
        # Occupation
        if any(w in lower for w in ['farmer', 'రైతు', 'agriculture']):
            params['occupation'] = 'farmer'
        
        # Scheme name
        scheme_map = {'kisan': 'pm_kisan', 'కిసాన్': 'pm_kisan', 'awas': 'pm_awas', 'ఆవాస్': 'pm_awas',
                      'ayushman': 'ayushman_bharat', 'ఆయుష్మాన్': 'ayushman_bharat', 'jan dhan': 'pm_jan_dhan',
                      'suraksha': 'pm_suraksha', 'సురక్ష': 'pm_suraksha', 'ujjwala': 'pm_ujjwala'}
        for kw, sid in scheme_map.items():
            if kw in lower:
                params['scheme_name'] = sid
                break
        
        return params
    
    def _planner(self, state: AgentState) -> AgentState:
        text = state["user_input"]
        lower = text.lower()
        
        params = self._extract_params(text)
        for k, v in self.user_context.items():
            if k not in params:
                params[k] = v
        self.user_context.update(params)
        state["extracted_params"] = params
        
        # Intent detection
        intent, requires_info, missing = "search", False, []
        
        if any(w in lower for w in ['hello', 'hi', 'నమస్కారం', 'హలో']):
            intent = "greet"
        elif any(w in lower for w in ['compare', 'vs', 'పోలిక']):
            intent = "compare"
        elif any(w in lower for w in ['how much', 'calculate', 'ఎంత']):
            intent = "calculate"
        elif any(w in lower for w in ['apply', 'process', 'దరఖాస్తు']):
            intent = "apply"
        elif any(w in lower for w in ['eligible', 'అర్హత', 'నాకు వస్తుందా']):
            intent = "eligibility"
            if 'scheme_name' not in params:
                missing.append('scheme_name')
            if 'age' not in params:
                missing.append('age')
            requires_info = bool(missing)
        elif any(w in lower for w in ['agriculture', 'health', 'housing', 'విభాగం']):
            intent = "sector"
        elif any(w in lower for w in ['all schemes', 'అన్ని యోజన', 'జాబితా']):
            intent = "all"
        
        state["intent"] = intent
        state["requires_info"] = requires_info
        state["missing_info"] = missing
        state["tool_to_use"] = {"search": "vector_search", "eligibility": "check_eligibility", "compare": "compare_schemes",
                                "calculate": "calculate_benefits", "apply": "get_application_steps", "sector": "get_schemes_by_sector",
                                "all": "get_all_schemes", "greet": "none"}.get(intent, "vector_search")
        return state
    
    def _ask_info(self, state: AgentState) -> AgentState:
        lang, missing = state["language"], state["missing_info"]
        questions = {
            "te": {'scheme_name': "ఏ యోజన కోసం?", 'age': "మీ వయస్సు?"},
            "en": {'scheme_name': "Which scheme?", 'age': "Your age?"}
        }
        response = "🤔 " + ("కొంత సమాచారం అవసరం:\n" if lang == "te" else "Need some info:\n")
        for info in missing:
            response += f"❓ {questions[lang].get(info, info)}\n"
        state["final_response"] = response
        return state
    
    def _executor(self, state: AgentState) -> AgentState:
        tool, text, lang, params = state["tool_to_use"], state["user_input"], state["language"], state["extracted_params"]
        
        if tool == "none":
            state["tool_results"] = ""
        elif tool == "vector_search":
            state["tool_results"] = self.vector_store.search(text, language=lang, n_results=3)
        elif tool == "check_eligibility":
            state["tool_results"] = check_eligibility.invoke({"scheme_name": params.get('scheme_name', text), 
                "age": params.get('age', 30), "annual_income": params.get('income', 100000), 
                "occupation": params.get('occupation'), "language": lang})
        elif tool == "compare_schemes":
            state["tool_results"] = compare_schemes.invoke({"scheme1": "PM Kisan", "scheme2": "PM Awas", "language": lang})
        elif tool == "calculate_benefits":
            state["tool_results"] = calculate_benefits.invoke({"scheme_name": params.get('scheme_name', text), "language": lang})
        elif tool == "get_application_steps":
            state["tool_results"] = get_application_steps.invoke({"scheme_name": params.get('scheme_name', text), "language": lang})
        elif tool == "get_schemes_by_sector":
            sector = next((s for s in ['agriculture', 'health', 'housing', 'finance', 'insurance', 'energy'] if s in text.lower()), "agriculture")
            state["tool_results"] = get_schemes_by_sector.invoke({"sector": sector, "language": lang})
        elif tool == "get_all_schemes":
            state["tool_results"] = get_all_schemes.invoke({"language": lang})
        else:
            state["tool_results"] = self.vector_store.search(text, language=lang)
        
        return state
    
    def _synthesizer(self, state: AgentState) -> AgentState:
        intent, lang, text, results = state["intent"], state["language"], state["user_input"], state["tool_results"]
        
        if intent == "greet":
            state["final_response"] = "నమస్కారం! 🙏 నేను NIVA. ఏ యోజన గురించి తెలుసుకోవాలి?" if lang == "te" else "Hello! 🙏 I'm NIVA. Which scheme would you like to know about?"
            return state
        
        prompt = f"""మీరు NIVA. తెలుగులో మాత్రమే 4-6 వాక్యాలలో సమాధానం ఇవ్వండి.
సమాచారం: {results}""" if lang == "te" else f"""You are NIVA. Reply in English only, 4-6 sentences.
Info: {results}"""
        
        response = self.llm.invoke([SystemMessage(content=prompt), HumanMessage(content=text)])
        state["final_response"] = response.content
        return state
    
    def process(self, user_input: str) -> dict:
        # Auto-detect language from input text (Telugu Unicode range check)
        has_telugu = any('\u0C00' <= c <= '\u0C7F' for c in user_input)
        lang = "te" if has_telugu else "en"
        
        state = {"user_input": user_input, "language": lang, "conversation_history": self.conversation_history,
                 "intent": "", "requires_info": False, "missing_info": [], "extracted_params": {},
                 "tool_to_use": "", "tool_results": "", "final_response": ""}
        
        final = self.graph.invoke(state)
        
        self.conversation_history.extend([{"role": "user", "content": user_input}, {"role": "assistant", "content": final["final_response"]}])
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        return {"response": final["final_response"], "language": lang, "intent": final["intent"]}
    
    def clear_history(self):
        self.conversation_history = []
        self.user_context = {}


SchemeAgent = AgentWorkflow
