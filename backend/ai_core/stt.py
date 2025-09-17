# backend/ai_core/stt.py

import whisper

# backend/ai_core/stt.py

import whisper
import numpy as np

class SpeechToText:
    def __init__(self, model_size="medium"):
        print(f"Memuat model STT Whisper ({model_size})...")
        self.model = whisper.load_model(model_size)
        print("Model STT Whisper berhasil dimuat.")

    def transcribe(self, audio_data: np.ndarray) -> str:
        try:
            audio_float32 = audio_data.astype(np.float32)

            result = self.model.transcribe(audio_float32, language="id", fp16=True)

            return result['text']
        except Exception as e:
            print(f"Error saat transkripsi audio: {e}")
            return ""