"""
Groq Whisper STT with local Telugu fallback.
Primary: Groq API (whisper-large-v3)
Fallback: Local Hugging Face model for Telugu
"""
import os
import tempfile
import numpy as np
from scipy.io import wavfile
from scipy import signal
from dotenv import load_dotenv

load_dotenv()


class GroqWhisperSTT:
    """Speech-to-Text using Groq Whisper API with local fallback."""
    
    def __init__(self, use_local_fallback: bool = True):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        
        from groq import Groq
        self.client = Groq(api_key=self.api_key)
        self.use_local_fallback = use_local_fallback
        self.local_model = None
        print("✅ Groq Whisper STT initialized!")
    
    def _load_local_model(self):
        """Load local Telugu Whisper model as fallback."""
        if self.local_model is None:
            print("Loading local Telugu model (vasista22/whisper-telugu-large-v2)...")
            from transformers import pipeline
            self.local_model = pipeline(
                "automatic-speech-recognition",
                model="vasista22/whisper-telugu-large-v2",
                device="cpu"
            )
            print("✅ Local Telugu model loaded!")
        return self.local_model
    
    def transcribe(self, audio_path: str, language: str = "te") -> dict:
        """Transcribe audio file using Groq API."""
        try:
            with open(audio_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    file=(audio_path, audio_file.read()),
                    model="whisper-large-v3",
                    language=language,
                    response_format="verbose_json"
                )
            return {"text": transcription.text, "language": language, "source": "groq"}
        except Exception as e:
            print(f"Groq API error: {e}")
            if self.use_local_fallback and language == "te":
                return self._transcribe_local(audio_path)
            return {"text": "", "language": language, "error": str(e)}
    
    def _transcribe_local(self, audio_path: str) -> dict:
        """Fallback to local Telugu model."""
        try:
            model = self._load_local_model()
            result = model(audio_path)
            return {"text": result["text"], "language": "te", "source": "local"}
        except Exception as e:
            return {"text": "", "language": "te", "error": str(e)}
    
    def transcribe_numpy(self, audio_data: np.ndarray, sample_rate: int = 16000, language: str = "te") -> dict:
        """Transcribe numpy audio array."""
        # Resample to 16kHz if needed
        if sample_rate != 16000:
            num_samples = int(len(audio_data) * 16000 / sample_rate)
            audio_data = signal.resample(audio_data, num_samples)
            sample_rate = 16000
        
        # Handle stereo
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)
        
        # Normalize
        if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
            audio_data = (audio_data * 32767).astype(np.int16)
        
        # Save to temp file and transcribe
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            wavfile.write(temp_path, sample_rate, audio_data)
        
        try:
            return self.transcribe(temp_path, language)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


# Alias for backward compatibility
WhisperSTT = GroqWhisperSTT
