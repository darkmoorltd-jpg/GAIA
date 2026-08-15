
import streamlit as st
import requests
import os
import tempfile

DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

def explain_diagnosis(diagnosis, confidence, crop_or_type, context_type="crop"):
    """Use DeepSeek to explain a GAIA diagnosis and provide comprehensive farming guidance."""
    if context_type == "crop":
        prompt = f"""GAIA diagnosed: {diagnosis} on {crop_or_type} with {confidence:.1f}% confidence.
Please provide a comprehensive farmer-friendly guide covering:
1. What This Means
2. Organic Treatment
3. Chemical Treatment
4. Pesticide/Herbicide Guide
5. Water Management
6. Ridges/Bed Preparation
7. Yield Impact
8. Cost Estimate
9. Prevention
10. Safety
Be practical, specific, and use Nigerian/local context. Mention exact product names available in Nigerian agro-dealers."""
    elif context_type == "pest":
        prompt = f"""GAIA identified: {diagnosis} with {confidence:.1f}% confidence.
Please provide a comprehensive pest management guide covering:
1. About This Pest
2. Organic Control
3. Chemical Pesticides
4. Herbicide Guide
5. Water & Irrigation
6. Field Management
7. Yield Protection
8. Cost-Benefit
9. Prevention
10. Safety
Be practical, specific, and use Nigerian/local context."""
    elif context_type == "soil":
        prompt = f"""GAIA identified soil type: {diagnosis} with {confidence:.1f}% confidence.
Please provide a comprehensive soil management guide covering:
1. Soil Characteristics
2. Organic Improvement
3. Fertilizer Guide
4. Best Crops
5. Water Management
6. Land Preparation
7. Yield Potential
8. Input Cost
9. Soil Conservation
10. Common Mistakes
Be practical, specific, and use Nigerian/local context."""
    elif context_type == "livestock":
        prompt = f"""GAIA diagnosed: {diagnosis} in livestock with {confidence:.1f}% confidence.

Please provide a comprehensive farmer-friendly guide covering:
1. **What This Means:** Explain the disease in simple terms
2. **Symptoms:** How to recognise it
3. **Isolation:** Should the animal be separated?
4. **Treatment:** Specific medicines, dosages, and administration
5. **Prevention:** Vaccinations, hygiene, and management
6. **Feeding:** Special nutrition during recovery
7. **Cost Estimate:** Approximate treatment cost
8. **Safety:** Handling sick animals, milk/meat withdrawal periods
Be practical, specific, and use Nigerian/local context. Mention exact product names available in Nigerian veterinary stores."""
    else:
        prompt = f"""GAIA diagnosis: {diagnosis}. Explain and give actionable advice."""
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are GAIA, an expert agricultural advisor built by Darkmoor Ltd in Nigeria. Give practical, specific, Nigerian-context answers. Never mention DeepSeek or any other AI company. You ARE GAIA."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }
    try:
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"], None
        return None, f"API error: {response.status_code}"
    except Exception as e:
        return None, str(e)


def text_to_speech(text, language="en"):
    """Convert text to speech using Edge TTS (free) with local voice selection."""
    import asyncio
    import edge_tts

    # Map language to preferred voice
    voices = {
        "en-GB": "en-GB-SoniaNeural",
        "en-US": "en-US-JennyNeural",
        "pcm": "en-GB-RyanNeural",     # Nigerian Pidgin
        "ha": "ha-NG-MuhammedNeural",  # Hausa
        "yo": "yo-NG-AbimbolaNeural",  # Yoruba
        "ig": "ig-NG-ChidinmaNeural",  # Igbo
    }
    voice = voices.get(language, "en-GB-SoniaNeural")

    # gTTS fallback languages
    gtts_lang = {
        "en-GB": "en",
        "en-US": "en",
        "pcm": "en",
        "ha": "ha",
        "yo": "yo",
        "ig": "ig",
    }.get(language, "en")

    async def generate_with_edge():
        communicate = edge_tts.Communicate(text, voice)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        await communicate.save(tmp.name)
        return tmp.name, None

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_path, error = loop.run_until_complete(generate_with_edge())
        loop.close()

        if error:
            # gTTS fallback
            from gtts import gTTS
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
            tts.save(tmp.name)
            with open(tmp.name, "rb") as f:
                audio_bytes = f.read()
            os.unlink(tmp.name)
            return audio_bytes, None

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        os.unlink(audio_path)
        return audio_bytes, None

    except Exception as e:
        # Last resort: gTTS
        try:
            from gtts import gTTS
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
            tts.save(tmp.name)
            with open(tmp.name, "rb") as f:
                audio_bytes = f.read()
            os.unlink(tmp.name)
            return audio_bytes, None
        except Exception as e2:
            return None, str(e2)
