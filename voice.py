"""Voice recognition module using GigaAM."""

import tempfile
import threading
import queue
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import sounddevice as sd
import soundfile as sf


class VoiceRecognizer:
    """Voice recognizer using GigaAM model."""

    def __init__(self, model_name: str = "v3_ctc"):
        self.model_name = model_name
        self.model = None
        self.is_recording = False
        self.audio_queue: queue.Queue = queue.Queue()
        self.sample_rate = 16000
        self.recorded_audio: list = []
        self._record_thread: Optional[threading.Thread] = None
        self._on_result: Optional[Callable[[str], None]] = None
        self._on_status: Optional[Callable[[str], None]] = None

    def load_model(self) -> bool:
        """Load the GigaAM model."""
        try:
            import gigaam
            self._update_status("Loading GigaAM model...")
            self.model = gigaam.load_model(self.model_name)
            self._update_status("GigaAM model loaded")
            return True
        except ImportError:
            self._update_status("GigaAM not installed. Run: pip install gigaam")
            return False
        except Exception as e:
            self._update_status(f"Failed to load model: {e}")
            return False

    def set_callbacks(
        self,
        on_result: Optional[Callable[[str], None]] = None,
        on_status: Optional[Callable[[str], None]] = None
    ):
        """Set callback functions for results and status updates."""
        self._on_result = on_result
        self._on_status = on_status

    def _update_status(self, status: str):
        """Update status via callback."""
        if self._on_status:
            self._on_status(status)

    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio recording."""
        if status:
            self._update_status(f"Audio error: {status}")
        if self.is_recording:
            self.recorded_audio.append(indata.copy())

    def start_recording(self):
        """Start recording audio."""
        if self.is_recording:
            return

        self.is_recording = True
        self.recorded_audio = []
        self._update_status("Recording...")

        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                callback=self._audio_callback
            )
            self.stream.start()
        except Exception as e:
            self._update_status(f"Failed to start recording: {e}")
            self.is_recording = False

    def stop_recording(self) -> Optional[str]:
        """Stop recording and transcribe."""
        if not self.is_recording:
            return None

        self.is_recording = False
        self._update_status("Processing...")

        try:
            self.stream.stop()
            self.stream.close()
        except Exception as e:
            self._update_status(f"Error stopping stream: {e}")

        if not self.recorded_audio:
            self._update_status("No audio recorded")
            return None

        # Concatenate all recorded audio
        audio_data = np.concatenate(self.recorded_audio, axis=0)

        # Transcribe
        transcription = self._transcribe(audio_data)

        if transcription and self._on_result:
            self._on_result(transcription)

        return transcription

    def _transcribe(self, audio_data: np.ndarray) -> Optional[str]:
        """Transcribe audio data using GigaAM."""
        if self.model is None:
            if not self.load_model():
                return None

        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
                sf.write(temp_path, audio_data, self.sample_rate)

            # Transcribe
            self._update_status("Transcribing...")
            transcription = self.model.transcribe(temp_path)

            # Clean up
            Path(temp_path).unlink(missing_ok=True)

            self._update_status("Ready")
            return transcription

        except Exception as e:
            self._update_status(f"Transcription error: {e}")
            return None

    def toggle_recording(self) -> bool:
        """Toggle recording state. Returns True if now recording."""
        if self.is_recording:
            self.stop_recording()
            return False
        else:
            self.start_recording()
            return True


# Simple test
if __name__ == "__main__":
    def on_result(text):
        print(f"Transcription: {text}")

    def on_status(status):
        print(f"Status: {status}")

    recognizer = VoiceRecognizer()
    recognizer.set_callbacks(on_result, on_status)

    print("Press Enter to start recording, Enter again to stop...")
    input()
    recognizer.start_recording()
    input()
    recognizer.stop_recording()
