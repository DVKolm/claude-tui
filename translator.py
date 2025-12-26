"""Text translation module using MarianMT."""

from typing import Optional, Callable


class Translator:
    """Russian to English translator using MarianMT."""

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self._on_status: Optional[Callable[[str], None]] = None

    def set_status_callback(self, callback: Callable[[str], None]):
        """Set callback for status updates."""
        self._on_status = callback

    def _update_status(self, status: str):
        if self._on_status:
            self._on_status(status)

    def load_model(self) -> bool:
        """Load the translation model."""
        try:
            self._update_status("Loading translator...")
            from transformers import MarianMTModel, MarianTokenizer

            model_name = "Helsinki-NLP/opus-mt-ru-en"
            self.tokenizer = MarianTokenizer.from_pretrained(model_name)
            self.model = MarianMTModel.from_pretrained(model_name)
            self._update_status("Translator ready")
            return True
        except Exception as e:
            self._update_status(f"Translator error: {e}")
            return False

    def translate(self, text: str) -> Optional[str]:
        """Translate Russian text to English."""
        if not text or not text.strip():
            return ""

        if self.model is None:
            if not self.load_model():
                return None

        try:
            inputs = self.tokenizer(text, return_tensors="pt", padding=True)
            translated = self.model.generate(**inputs)
            result = self.tokenizer.decode(translated[0], skip_special_tokens=True)
            return result
        except Exception as e:
            self._update_status(f"Translation error: {e}")
            return None


# Singleton instance
_translator: Optional[Translator] = None


def get_translator() -> Translator:
    """Get or create translator instance."""
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator


# Simple test
if __name__ == "__main__":
    translator = get_translator()
    translator.set_status_callback(print)

    test_phrases = [
        "Привет, как дела?",
        "Сегодня хорошая погода",
        "Я программирую на Python",
    ]

    for phrase in test_phrases:
        result = translator.translate(phrase)
        print(f"{phrase} -> {result}")
