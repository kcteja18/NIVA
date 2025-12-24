"""
Text-to-Speech module using Edge-TTS.
Supports Telugu and English with natural neural voices.
"""
import edge_tts
import asyncio
import os

# Voice mappings for Telugu and English
VOICES = {
    "te": {
        "female": "te-IN-ShrutiNeural",
        "male": "te-IN-MohanNeural"
    },
    "en": {
        "female": "en-US-AriaNeural",
        "male": "en-US-GuyNeural"
    }
}

class EdgeTTS:
    def __init__(self, default_language="te", default_gender="female"):
        """
        Initialize Edge TTS.
        
        Args:
            default_language: Default language code ('te' or 'en')
            default_gender: Default voice gender ('female' or 'male')
        """
        self.default_language = default_language
        self.default_gender = default_gender
        print(f"✅ TTS initialized with {default_language} {default_gender} voice")
    
    async def _synthesize_async(self, text, output_path, language=None, gender=None):
        """Internal async method to synthesize speech."""
        lang = language or self.default_language
        gend = gender or self.default_gender
        
        # Get voice
        voice = VOICES.get(lang, {}).get(gend, VOICES["en"]["female"])
        
        # Create communicate object
        communicate = edge_tts.Communicate(text, voice)
        
        # Save audio
        await communicate.save(output_path)
    
    def synthesize(self, text, output_path="output.mp3", language=None, gender=None):
        """
        Synthesize text to speech and save to file.
        
        Args:
            text: Text to synthesize
            output_path: Path to save audio file
            language: Language code ('te' or 'en'), None uses default
            gender: Voice gender ('female' or 'male'), None uses default
        
        Returns:
            Path to generated audio file
        """
        try:
            # Run async synthesis
            asyncio.run(self._synthesize_async(text, output_path, language, gender))
            return output_path
        except Exception as e:
            print(f"❌ TTS error: {e}")
            return None
    
    def speak_telugu(self, text, output_path="output_te.mp3"):
        """Convenience method for Telugu speech."""
        return self.synthesize(text, output_path, language="te")
    
    def speak_english(self, text, output_path="output_en.mp3"):
        """Convenience method for English speech."""
        return self.synthesize(text, output_path, language="en")


# Test module
if __name__ == "__main__":
    print("Testing Edge TTS module...")
    
    tts = EdgeTTS(default_language="te")
    
    # Test Telugu
    print("\nGenerating Telugu audio...")
    tts.speak_telugu("నమస్కారం, నేను మీ సహాయం చేయగలను")
    print("✅ Telugu audio generated: output_te.mp3")
    
    # Test English
    print("\nGenerating English audio...")
    tts.speak_english("Hello, I can help you with government schemes")
    print("✅ English audio generated: output_en.mp3")
