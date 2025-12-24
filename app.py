"""
NIVA - Voice-Based Government Scheme Assistant
Gradio UI with bilingual support (Telugu + English)
"""
import gradio as gr
import os
import sys
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.groq_stt import GroqWhisperSTT
from src.tts import EdgeTTS
from src.langgraph_agent import AgentWorkflow

# Global instances
stt_model = None
tts_model = None
agent = None
chat_history = []  # Store chat messages for display

def initialize_models():
    """Initialize all AI models."""
    global stt_model, tts_model, agent
    
    if stt_model is None:
        print("Loading Groq Whisper STT...")
        stt_model = GroqWhisperSTT(use_local_fallback=True)
        print("✅ STT loaded!")
    
    if tts_model is None:
        print("Loading Edge TTS...")
        tts_model = EdgeTTS()
        print("✅ Edge TTS loaded!")
    
    if agent is None:
        print("Initializing LangGraph Agent with ChromaDB...")
        agent = AgentWorkflow()
        print("✅ LangGraph Agent initialized!")
    
    return "✅ All models loaded successfully!"

def process_audio(audio_input, language_choice):
    """
    Process audio input through the full pipeline:
    1. STT (Speech to Text)
    2. Agent (Process query)
    3. TTS (Text to Speech)
    """
    global chat_history
    
    try:
        # Initialize if needed
        if stt_model is None or agent is None or tts_model is None:
            error_msg = "⚠️ Please click 'Initialize Models' first!"
            error_history = format_chat_history(chat_history + [("assistant", error_msg, "en")])
            return error_history, "", None
        
        if audio_input is None:
            error_history = format_chat_history(chat_history)
            return error_history, "", None
        
        # Get audio data
        sample_rate, audio_data = audio_input
        
        # Convert to float32 and normalize
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32) / 32768.0
        
        # Transcribe - pass actual sample_rate from Gradio
        lang_code = "te" if language_choice == "Telugu (తెలుగు)" else "en"
        transcription = stt_model.transcribe_numpy(audio_data, sample_rate=sample_rate, language=lang_code)
        user_text = transcription["text"]
        detected_lang = transcription.get("language", lang_code)
        
        if not user_text:
            error_msg = "❌ Could not understand audio. Please try again."
            error_history = format_chat_history(chat_history + [("assistant", error_msg, "en")])
            return error_history, "", None
        
        # Process through agent - force language from user selection
        agent.current_language = lang_code
        result = agent.process(user_text)
        agent_response = result["response"]
        detected_lang = lang_code
        
        # Generate audio response
        output_path = "temp_output.mp3"
        try:
            tts_model.synthesize(agent_response, output_path, language=detected_lang)
        except Exception as tts_error:
            print(f"TTS Error: {tts_error}")
            output_path = None
        
        # Add to chat history
        chat_history.append(("user", user_text, detected_lang))
        chat_history.append(("assistant", agent_response, detected_lang))
        
        formatted_history = format_chat_history(chat_history)
        return formatted_history, "", output_path
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = f"❌ Error: {str(e)}"
        chat_history.append(("assistant", error_msg, "en"))
        formatted_history = format_chat_history(chat_history)
        return formatted_history, "", None

def process_text(text_input, language_choice):
    """Process text input (fallback option)."""
    global chat_history
    
    print(f"\n{'='*50}")
    print(f"Processing text input: {text_input}")
    print(f"Language choice: {language_choice}")
    print(f"Agent initialized: {agent is not None}")
    print(f"TTS initialized: {tts_model is not None}")
    print(f"{'='*50}\n")
    
    try:
        if agent is None or tts_model is None:
            error_msg = "⚠️ Please click 'START' button first to initialize models!"
            print(f"ERROR: Models not initialized")
            error_history = format_chat_history(chat_history + [("assistant", error_msg, "en")])
            return error_history, "", None
        
        if not text_input or text_input.strip() == "":
            formatted_history = format_chat_history(chat_history)
            return formatted_history, text_input, None
        
        # Process through agent - force language from user selection
        lang_code = "te" if language_choice == "Telugu (తెలుగు)" else "en"
        print(f"Using language code: {lang_code}")
        agent.current_language = lang_code
        
        print("Calling agent.process()...")
        result = agent.process(text_input)
        agent_response = result["response"]
        detected_lang = lang_code
        
        print(f"Agent response: {agent_response[:100]}...")
        
        # Generate audio response
        output_path = "temp_output_text.mp3"
        try:
            print("Generating TTS audio...")
            tts_model.synthesize(agent_response, output_path, language=detected_lang)
            print("TTS audio generated successfully")
        except Exception as tts_error:
            print(f"TTS Error: {tts_error}")
            output_path = None
        
        # Add to chat history
        chat_history.append(("user", text_input, detected_lang))
        chat_history.append(("assistant", agent_response, detected_lang))
        
        print(f"Chat history length: {len(chat_history)}")
        
        formatted_history = format_chat_history(chat_history)
        print(f"Formatted history: {formatted_history}")
        
        return formatted_history, "", output_path
        
    except Exception as e:
        import traceback
        print(f"\n{'!'*50}")
        print("EXCEPTION in process_text:")
        traceback.print_exc()
        print(f"{'!'*50}\n")
        error_msg = f"❌ Error: {str(e)}"
        chat_history.append(("assistant", error_msg, "en"))
        formatted_history = format_chat_history(chat_history)
        return formatted_history, "", None

def clear_conversation():
    """Clear conversation history."""
    global chat_history
    chat_history = []
    if agent:
        agent.clear_history()
    return [], "", None, None

def format_chat_history(history):
    """Format chat history for display in chatbot (Gradio 6.2 dictionary format)."""
    formatted = []
    for role, message, lang in history:
        formatted.append({
            "role": role if role == "user" else "assistant",
            "content": message
        })
    return formatted

# Create Gradio interface with modern, friendly design
with gr.Blocks(
    title="NIVA - నివా (Native Indian Voice Agent)",
    theme=gr.themes.Default(
        primary_hue="indigo",
        secondary_hue="blue",
        neutral_hue="slate",
    ),
    css="""
        .gradio-container {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%) !important;
            min-height: 100vh;
        }
        .main-header {
            text-align: center;
            padding: 40px 20px;
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: #ffffff !important;
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            border: 2px solid rgba(59, 130, 246, 0.5);
        }
        .main-header h1, .main-header p {
            color: #ffffff !important;
        }
        .main-content {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(59, 130, 246, 0.3);
        }
        .sidebar {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            padding: 20px;
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(59, 130, 246, 0.3);
        }
        .example-card {
            background: linear-gradient(135deg, #475569 0%, #64748b 100%);
            padding: 15px;
            border-radius: 12px;
            margin: 10px 0;
            border-left: 5px solid #3b82f6;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            color: #ffffff !important;
        }
        .example-card b {
            color: #60a5fa !important;
            font-size: 1.1em;
        }
        .example-card code {
            background: #1e293b;
            padding: 4px 8px;
            border-radius: 6px;
            color: #93c5fd !important;
            font-weight: 600;
        }
        .example-card small {
            color: #cbd5e1 !important;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #60a5fa !important;
        }
        p, span, div, label {
            color: #e2e8f0 !important;
        }
        .markdown-text {
            color: #e2e8f0 !important;
        }
        .gr-button-primary {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            border: none !important;
            color: white !important;
            font-weight: 600 !important;
        }
        .gr-button-secondary {
            background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%) !important;
            color: white !important;
            font-weight: 600 !important;
        }
        .gr-input, .gr-textbox, .gr-dropdown {
            background: #1e293b !important;
            color: #e2e8f0 !important;
            border: 1px solid #475569 !important;
        }
    """
) as demo:
    
    # Beautiful Header
    gr.HTML("""
        <div class="main-header">
            <h1 style="margin: 0; font-size: 2.8em; color: #ffffff !important;">🏛️ NIVA - నివా (Native Indian Voice Agent)</h1>
            <p style="margin: 15px 0 0 0; font-size: 1.3em; color: #ffffff !important; font-weight: 600;">
                Your AI Assistant for Government Schemes
            </p>
            <p style="margin: 8px 0 0 0; font-size: 1em; color: #e0e7ff !important;">
                🎤 Speak in Telugu or English
            </p>
        </div>
    """)
    
    # Main Container
    with gr.Row():
        # Left: Chat Area (70%)
        with gr.Column(scale=7, elem_classes="main-content"):
            # Initialization Section
            with gr.Row():
                init_btn = gr.Button(
                    "🚀 START - Click Here First!",
                    variant="primary",
                    size="lg",
                    scale=3
                )
                language_select = gr.Dropdown(
                    choices=["Telugu (తెలుగు)", "English"],
                    value="Telugu (తెలుగు)",
                    label="🌐 Choose Language",
                    scale=2
                )
            
            init_status = gr.Textbox(
                label="Status",
                show_label=True,
                container=True,
                interactive=False,
                placeholder="Click START button to initialize models..."
            )
            
            gr.Markdown("---")
            
            # Chat Display
            chatbot = gr.Chatbot(
                label="💬 Chat with NIVA",
                height=450,
                show_label=True
            )
            
            # Text Input Row
            with gr.Row():
                text_input = gr.Textbox(
                    placeholder="💬 Type your question here... (e.g., రైతు యోజనలు చెప్పండి)",
                    show_label=False,
                    scale=5,
                    container=False
                )
                send_btn = gr.Button(
                    " Send",
                    variant="primary",
                    scale=1
                )
            
            # Voice Input (Collapsible)
            with gr.Accordion("🎤 Or Use Voice Input", open=False):
                with gr.Row():
                    audio_input = gr.Audio(
                        sources=["microphone", "upload"],
                        type="numpy",
                        label="Record or Upload Audio"
                    )
                with gr.Row():
                    voice_btn = gr.Button("🗣️ Send Voice Message", variant="secondary", size="lg")
            
            # Audio Output
            with gr.Accordion("🔊 Audio Response", open=False):
                audio_output = gr.Audio(
                    label="Listen to response",
                    type="filepath",
                    interactive=False
                )
            
            # Action Buttons
            with gr.Row():
                clear_btn = gr.Button("🗑️ Clear Chat", size="sm", variant="stop")
        
        # Right: Helpful Info (30%)
        with gr.Column(scale=3, elem_classes="sidebar"):
            gr.Markdown("""
            ### 🎯 How to Use
            
            **1.** Click **START** button ⬆️  
            **2.** Wait for models to load  
            **3.** Choose your language  
            **4.** Type or speak your question  
            **5.** Get instant AI response!
            """)
            
            gr.Markdown("---")
            
            # Quick Examples in Cards
            gr.HTML("""
                <div class="example-card">
                    <b style="font-size: 1.1em;">📝 Telugu Examples:</b><br><br>
                    <code>రైతు యోజనలు చెప్పండి</code><br>
                    <small>Tell me about farmer schemes</small><br><br>
                    
                    <code>అన్ని యోజనలు చూపించండి</code><br>
                    <small>Show all schemes</small><br><br>
                    
                    <code>నేను రైతును, వయస్సు 35</code><br>
                    <small>I am a farmer, age 35</small>
                </div>
                
                <div class="example-card">
                    <b style="font-size: 1.1em;">📝 English Examples:</b><br><br>
                    <code>Tell me about health schemes</code><br><br>
                    
                    <code>Am I eligible for PM Kisan?</code><br><br>
                    
                    <code>Show all available schemes</code>
                </div>
            """)
            
            gr.Markdown("---")
            
            gr.Markdown("""
            ### 📊 Available Schemes
            
            🌾 **PM Kisan** - Farmer Support  
            🏠 **PM Awas** - Housing  
            🏥 **Ayushman Bharat** - Healthcare  
            💰 **PM Jan Dhan** - Banking  
            🛡️ **PM Suraksha** - Insurance  
            ⚡ **PM Ujjwala** - Energy  
            """)
            
            gr.Markdown("---")
            
            gr.Markdown("""
            ### ✨ Features
            
            ✅ Voice & Text Support  
            ✅ Bilingual (Telugu + English)  
            ✅ Smart AI Responses  
            ✅ Eligibility Checking  
            ✅ Conversation Memory  
            ✅ 100% Free to Use  
            """)
    
    # Footer
    gr.Markdown("""
    ---
    <center>
    <p style="color: #94a3b8 !important; font-size: 0.95em; font-weight: 500;">
    Powered by Groq (Llama 3.1) • OpenAI Whisper • Edge-TTS<br>
    Built for Indian Citizens
    </p>
    </center>
    """)
    
    # Event handlers
    init_btn.click(
        fn=initialize_models,
        outputs=init_status
    )
    
    send_btn.click(
        fn=process_text,
        inputs=[text_input, language_select],
        outputs=[chatbot, text_input, audio_output]
    )
    
    text_input.submit(
        fn=process_text,
        inputs=[text_input, language_select],
        outputs=[chatbot, text_input, audio_output]
    )
    
    voice_btn.click(
        fn=process_audio,
        inputs=[audio_input, language_select],
        outputs=[chatbot, text_input, audio_output]
    )
    
    clear_btn.click(
        fn=clear_conversation,
        outputs=[chatbot, text_input, audio_input, audio_output]
    )

# Launch the app
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Starting NIVA - Government Scheme Assistant")
    print("="*60)
    print("\n📍 Local URL: http://localhost:7860")
    print("🌐 Public URL: Will be generated...\n")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        show_error=True,
        inbrowser=True
    )
