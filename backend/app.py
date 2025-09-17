# backend/app.py

import os
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import Dict
import numpy as np
import soundfile as sf
import io

from ai_core.stt import SpeechToText
from ai_core.nlu import NLU
from ai_core.dialogue_manager import DialogueManager
from ai_core.action_executor import ActionExecutor
from ai_core.tts import TextToSpeech

print("--- Memulai Inisialisasi Backend Asisten AI ---")
app = FastAPI(
    title="Asisten AI Desktop Backend",
    description="API untuk mengelola semua fungsionalitas AI.",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Buat direktori jika belum ada
if not os.path.exists('uploads'):
    os.makedirs('uploads')
if not os.path.exists('outputs'):
    os.makedirs('outputs')

modules: Dict[str, object] = {}

@app.on_event("startup")
async def startup_event():
    print("--- Memuat Model AI... ---")
    modules["stt"] = SpeechToText(model_size="base")
    modules["dialogue_manager"] = DialogueManager()
    modules["action_executor"] = ActionExecutor()
    modules["tts"] = TextToSpeech()
    print("--- Inisialisasi Selesai. Server Siap. ---")


class ProcessTextRequest(BaseModel):
    text: str

class SynthesizeRequest(BaseModel):
    text: str


@app.post("/api/transcribe", summary="Mentranskripsikan file audio")
async def transcribe_audio(audio: UploadFile = File(...)):
    try:
        audio_bytes = await audio.read()

        audio_data, samplerate = sf.read(io.BytesIO(audio_bytes))

        transcribed_text = await run_in_threadpool(modules["stt"].transcribe, audio_data=audio_data)
        
        return {"text": transcribed_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi error saat memproses audio: {str(e)}")

@app.post("/api/process-text", summary="Memproses teks untuk mendapatkan respons")
async def process_text(request: ProcessTextRequest):
    try:
        def sync_pipeline(text: str):
            dm_result = modules["dialogue_manager"].process(text)
            
            if dm_result['type'] == 'response':
                return dm_result['message']
            elif dm_result['type'] == 'action':
                return modules["action_executor"].execute(dm_result['data'])
            else:
                return "Terjadi kesalahan pada alur logika."

        response_message = await run_in_threadpool(sync_pipeline, text=request.text)
        
        return {"response": response_message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi error saat memproses teks: {str(e)}")


@app.post("/api/synthesize", summary="Menghasilkan ucapan dari teks")
async def synthesize_speech(request: SynthesizeRequest):
    output_path = "outputs/response.wav"
    try:
        await run_in_threadpool(modules["tts"].synthesize, text=request.text, output_path=output_path)

        if os.path.exists(output_path):
            return FileResponse(output_path, media_type='audio/wav', filename='response.wav')
        else:
            raise HTTPException(status_code=500, detail="Gagal membuat file audio.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi error saat sintesis ucapan: {str(e)}")

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=5000)