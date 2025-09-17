# run_assistant.py

import os
import struct
import pvporcupine
import pyaudio
import sounddevice as sd
import soundfile as sf
import requests
import time
from dotenv import load_dotenv
import numpy as np

load_dotenv(dotenv_path=os.path.join('backend', '.env'))

PICOVOICE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY")
WAKE_WORD_MODEL_PATH = "backend/Wake_word_model/halo-Kina_en_windows_v3_0_0.ppn" 
BACKEND_URL = "http://127.0.0.1:5000"
SAMPLE_RATE = 16000
RECORD_SECONDS = 5 

class WakeWordListener:
    def __init__(self):
        self.porcupine = pvporcupine.create(
            access_key=PICOVOICE_ACCESS_KEY,
            keyword_paths=[WAKE_WORD_MODEL_PATH]
        )
        self.pa = pyaudio.PyAudio()
        self.audio_stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )
        self.is_listening = True

    def listen(self):
        print("Pendengar 'halo Kina' aktif...")
        while self.is_listening:
            pcm = self.audio_stream.read(self.porcupine.frame_length)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            
            keyword_index = self.porcupine.process(pcm)
            if keyword_index >= 0:
                print("'halo Kina' terdeteksi! Mulai merekam perintah...")
                self.trigger_assistant()

    def trigger_assistant(self):
        print("Memicu asisten...")
        
        try:
            samplerate = 44100  
            duration = 0.2  
            frequency = 880.0  
            
            t = np.linspace(0., duration, int(samplerate * duration), endpoint=False)
            amplitude = 0.5
            audio_data = amplitude * np.sin(2. * np.pi * frequency * t)
            
            sd.play(audio_data, samplerate, blocking=True)
        except Exception as e:
            print(f"Gagal memainkan suara notifikasi: {e}")
        
        time.sleep(0.3)

        print(f"Merekam selama {RECORD_SECONDS} detik...")
        recording = sd.rec(int(RECORD_SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
        sd.wait() 
        
        temp_audio_path = "command.wav"
        sf.write(temp_audio_path, recording, SAMPLE_RATE, subtype='PCM_16')
        print("Perekaman selesai.")

        try:
            print("Mengirim audio ke backend untuk transkripsi...")
            with open(temp_audio_path, 'rb') as f:
                files = {'audio': (temp_audio_path, f, 'audio/wav')}
                response = requests.post(f"{BACKEND_URL}/api/transcribe", files=files)
                response.raise_for_status()
                transcribed_text = response.json().get('text')
                print(f"Hasil Transkripsi: '{transcribed_text}'")

            if not transcribed_text:
                raise ValueError("Transkripsi gagal atau kosong.")

            print("Mengirim teks ke backend untuk diproses...")
            response = requests.post(f"{BACKEND_URL}/api/process-text", json={"text": transcribed_text})
            response.raise_for_status()
            assistant_response_text = response.json().get('response')
            print(f"Respons Asisten: '{assistant_response_text}'")

            print("Meminta backend untuk menghasilkan suara...")
            response = requests.post(f"{BACKEND_URL}/api/synthesize", json={"text": assistant_response_text})
            response.raise_for_status()
            
            response_audio_path = "response.wav"
            with open(response_audio_path, 'wb') as f:
                f.write(response.content)
            
            data, fs = sf.read(response_audio_path, dtype='float32')
            sd.play(data, fs, blocking=True)

        except requests.exceptions.RequestException as e:
            print(f"Error komunikasi dengan backend: {e}")
        except Exception as e:
            print(f"Terjadi error pada alur asisten: {e}")
        finally:
            if os.path.exists(temp_audio_path):
                print(f"File audio sementara disimpan di: {temp_audio_path}") 
            if os.path.exists("response.wav"):
                os.remove("response.wav")
            
            print("\nKembali mendengarkan 'halo Kina'...")


    def stop(self):
        self.is_listening = False
        if self.porcupine:
            self.porcupine.delete()
        if self.audio_stream:
            self.audio_stream.close()
        if self.pa:
            self.pa.terminate()

if __name__ == "__main__":
    listener = WakeWordListener()
    try:
        listener.listen()
    except KeyboardInterrupt:
        print("Menghentikan listener...")
        listener.stop()