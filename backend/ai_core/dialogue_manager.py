# backend/ai_core/dialogue_manager.py

import google.generativeai as genai
import json

class DialogueManager:
    def __init__(self):
        self.history = []
        
        self.model = genai.GenerativeModel('models/gemini-2.5-pro')

        self.system_prompt = self._build_system_prompt()
        print("Dialogue Manager berbasis LLM siap.")

    def _build_system_prompt(self):
        """Membangun instruksi sistem dasar untuk LLM."""
        return """
        Anda adalah otak dari asisten AI desktop. Peran Anda adalah sebagai orchestrator.
        Berdasarkan percakapan dan perintah pengguna, tentukan tindakan selanjutnya.
        Anda memiliki akses ke alat-alat berikut:

        1. `open_app(app_name: str)`: Membuka aplikasi di komputer.
        2. `close_app(app_name: str)`: Menutup aplikasi yang sedang berjalan.
        3. `play_spotify(track_name: str)`: Mencari dan memainkan lagu di Spotify.
        4. `search_web(query: str)`: Mencari informasi di Google (gunakan ini jika pengguna hanya ingin mencari, bukan membuka situs spesifik).
        5. `information_retrieval(question: str)`: Menjawab pertanyaan pengetahuan umum secara mendalam.
        6. `set_volume(level: int)`: Mengatur volume sistem ke persentase tertentu (0-100).
        7. `mute_volume(mute: bool)`: Mematikan (true) atau menyalakan (false) suara sistem.
        8. `take_screenshot(path: str)`: Mengambil tangkapan layar dan menyimpannya ke path yang diberikan.
        9. `Maps_browser(browser: str, url: str)`: Membuka browser spesifik (seperti 'chrome' atau 'firefox') dan menavigasi ke URL yang diberikan.
        10. `new_tab_and_navigate(url: str)`: Di browser yang sedang aktif, membuka tab baru dan menavigasi ke URL yang diberikan.

        Aturan:
        - Jika perintah pengguna dapat dipenuhi oleh salah satu alat, respons Anda HARUS HANYA berupa objek JSON tunggal dengan format: `{"tool_call": {"name": "nama_alat", "parameters": {"nama_parameter": "nilai"}}}`.
        - Jika perintah pengguna adalah pertanyaan umum, salam, atau percakapan yang tidak memerlukan alat, respons Anda HARUS HANYA berupa objek JSON tunggal dengan format: `{"final_answer": "jawaban Anda dalam bentuk teks"}`.
        - Jangan menambahkan penjelasan apa pun di luar format JSON.
        """

    def process(self, user_text: str) -> dict:
        self.history.append({"role": "user", "text": user_text})

        full_prompt = self.system_prompt + "\n\nRiwayat Percakapan:\n"
        for turn in self.history:
            full_prompt += f"- {turn['role']}: {turn['text']}\n"
        
        try:
            response_text = self.model.generate_content(full_prompt).text
            response_text = response_text.strip().replace("```json", "").replace("```", "").strip()
            decision = json.loads(response_text)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error memproses respons LLM: {e}\nMencoba menjawab langsung...")
            return {"type": "response", "message": "Maaf, terjadi sedikit gangguan di otak saya. Bisa ulangi lagi?"}

        if "tool_call" in decision:
            tool_name = decision["tool_call"]["name"]
            parameters = decision["tool_call"]["parameters"]
            
            action_intent = tool_name 
            
            self.history.append({"role": "assistant", "text": f"Menggunakan alat: {tool_name} dengan parameter {parameters}"})
            
            return {"type": "action", "data": {"action": action_intent, "parameters": parameters}}
        
        elif "final_answer" in decision:
            response_message = decision["final_answer"]
            self.history.append({"role": "assistant", "text": response_message})
            return {"type": "response", "message": response_message}
            
        else:
            self.history.append({"role": "assistant", "text": "Format keputusan tidak dikenali."})
            return {"type": "response", "message": "Saya tidak yakin apa yang harus dilakukan."}

    def reset(self):
        self.history = []