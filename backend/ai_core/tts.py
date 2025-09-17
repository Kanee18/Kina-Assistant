from TTS.api import TTS
import torch
import os

from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import XttsAudioConfig
from TTS.config.shared_configs import BaseDatasetConfig
from TTS.tts.models.xtts import XttsArgs 
from torch.serialization import add_safe_globals

add_safe_globals([XttsConfig, XttsAudioConfig, BaseDatasetConfig, XttsArgs])

class TextToSpeech:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Memuat model TTS (Coqui TTS) ke {self.device}...")
        
        self.model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        try:
            self.tts = TTS(self.model_name).to(self.device)
            print("Model TTS berhasil dimuat.")
        except Exception as e:
            print(f"Gagal memuat model TTS: {e}. Fitur TTS mungkin tidak berfungsi.")
            self.tts = None

    def synthesize(self, text: str, output_path: str):
        if not self.tts:
            print("Model TTS tidak tersedia.")
            return

        speaker_sample_path = "youtube_voice.wav"

        if not os.path.exists(speaker_sample_path):
            print(f"Error: File sampel suara '{speaker_sample_path}' tidak ditemukan.")
            raise FileNotFoundError(f"File sampel suara '{speaker_sample_path}' tidak ditemukan.")

        try:
            self.tts.tts_to_file(
                text=text,
                file_path=output_path,
                speaker_wav=speaker_sample_path,
                language="en" 
            )
            print(f"Audio berhasil disimpan di {output_path}")
        except Exception as e:
            print(f"Tipe error saat sintesis: {type(e)}")
            print(f"Error saat sintesis ucapan dengan Coqui TTS: {e}")
            raise e