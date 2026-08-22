import requests
import json
from backend.config import settings
from typing import Tuple, Optional, Generator

class DeepSeekService:
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.url = "https://api.deepseek.com/v1/chat/completions"

    def explain_diagnosis(self, diagnosis: str, confidence: float, crop: str, context_type: str) -> Tuple[Optional[str], Optional[str]]:
        prompt = self._build_prompt(diagnosis, confidence, crop, context_type)
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are GAIA, an expert agricultural advisor built by Darkmoor Ltd in Nigeria."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }
        try:
            r = requests.post(self.url, headers=headers, json=payload, timeout=60)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"], None
            return None, f"API error: {r.status_code}"
        except Exception as e:
            return None, str(e)

    def _build_prompt(self, diagnosis: str, confidence: float, crop: str, context_type: str) -> str:
        if context_type == "pest":
            return f"""GAIA identified: {diagnosis} with {confidence:.1f}% confidence.
Provide a comprehensive pest management guide covering: About This Pest, Organic Control, Chemical Pesticides, Field Management, Prevention, Safety."""
        elif context_type == "soil":
            return f"""GAIA identified soil type: {diagnosis} with {confidence:.1f}% confidence.
Provide a comprehensive soil management guide covering: Soil Characteristics, Organic Improvement, Fertilizer Guide, Best Crops, Water Management."""
        else:
            return f"""GAIA diagnosed: {diagnosis} on {crop} with {confidence:.1f}% confidence.
Provide a comprehensive farmer-friendly guide covering: What This Means, Organic Treatment, Chemical Treatment, Water Management, Prevention, Safety."""
