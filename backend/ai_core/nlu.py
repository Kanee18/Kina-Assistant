# backend/ai_core/nlu.py

from transformers import pipeline

class NLU:
    def __init__(self):
        print("Memuat model NLU untuk Bahasa Indonesia...")
        model_name = "cahya/bert-base-indonesian-NER"
        self.ner_pipeline = pipeline(
            "ner", 
            model=model_name, 
            tokenizer=model_name, 
            grouped_entities=True,
            device=0  
        )
        print("Model NLU berhasil dimuat di GPU.")

    def process(self, text: str) -> dict:
        text = text.lower()
        
        intent = self._recognize_intent(text)
        
        entities = self._extract_entities(text, intent)

        return {"intent": intent, "entities": entities}

    def _recognize_intent(self, text: str) -> str:
        if "mainkan" in text and ("spotify" in text or "lagu" in text):
            return "play_spotify"
        if "buka" in text or "jalankan" in text:
            return "open_app"
        if "tutup" in text:
            return "close_app"
        if "cari" in text or "carikan" in text:
            return "search_web"
        return "information_retrieval"
        
    def _extract_entities(self, text: str, intent: str) -> dict:
        entities = {}
        if intent == "play_spotify":
            payload = text.replace("mainkan", "").replace("di spotify", "").replace("lagu", "").strip()
            entities['track_name'] = payload
        elif intent == "open_app":
            payload = text.replace("buka", "").replace("jalankan", "").strip()
            entities['app_name'] = payload
        elif intent == "close_app":
            payload = text.replace("tutup", "").strip()
            entities['app_name'] = payload
        elif intent == "search_web":
            payload = text.replace("cari", "").replace("carikan", "").strip()
            entities['query'] = payload
        elif intent == "information_retrieval":
            entities['question'] = text
            
        return entities