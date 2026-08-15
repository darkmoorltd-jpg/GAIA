
import streamlit as st
import requests
import os
import tempfile
import time
import json

DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

def explain_diagnosis(diagnosis, confidence, crop_or_type, context_type="crop"):
    """Stream a GAIA diagnosis explanation using st.write_stream."""
    if context_type == "crop":
        prompt = f"""GAIA diagnosed: {diagnosis} on {crop_or_type} with {confidence:.1f}% confidence.
Provide a comprehensive farmer-friendly guide covering:
1. What This Means
2. Organic Treatment
3. Chemical Treatment
4. Water Management
5. Ridges/Bed Preparation
6. Yield Impact
7. Cost Estimate
8. Prevention
9. Safety
Be practical, specific, and use Nigerian/local context. Mention exact product names available in Nigerian agro-dealers."""
    elif context_type == "pest":
        prompt = f"""GAIA identified: {diagnosis} with {confidence:.1f}% confidence.
Provide a comprehensive pest management guide covering:
1. About This Pest
2. Organic Control
3. Chemical Pesticides
4. Water & Irrigation
5. Field Management
6. Yield Protection
7. Cost-Benefit
8. Prevention
9. Safety
Be practical, specific, and use Nigerian/local context."""
    elif context_type == "soil":
        prompt = f"""GAIA identified soil type: {diagnosis} with {confidence:.1f}% confidence.
Provide a comprehensive soil management guide covering:
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
Provide a comprehensive farmer-friendly guide covering:
1. What This Means
2. Symptoms
3. Isolation
4. Treatment
5. Prevention
6. Feeding
7. Cost Estimate
8. Safety
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
        "max_tokens": 4000,
        "stream": True  # <-- enable streaming
    }

    def generate():
        for attempt in range(3):
            try:
                with requests.post(
                    DEEPSEEK_URL,
                    headers=headers,
                    json=payload,
                    stream=True,
                    timeout=120
                ) as response:
                    if response.status_code != 200:
                        yield f"API error: {response.status_code}"
                        return
                    for line in response.iter_lines():
                        if not line:
                            continue
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                return
                            try:
                                chunk = json.loads(data)
                                delta = chunk['choices'][0].get('delta', {}).get('content', '')
                                if delta:
                                    yield delta
                            except:
                                continue
                break
            except requests.exceptions.Timeout:
                if attempt == 2:
                    yield "DeepSeek timed out. Please try again."
                    return
                time.sleep(1)
                continue
            except Exception as e:
                yield f"Error: {str(e)}"
                return

    # Use st.write_stream to display tokens as they arrive
    answer = st.write_stream(generate())
    return answer, None


def text_to_speech(text, language="en"):
    """Convert text to speech using Edge TTS (free) with local voice selection."""
    import asyncio
    import edge_tts

    voices = {
        "en-GB": "en-GB-SoniaNeural",
        "en-US": "en-US-JennyNeural",
        "pcm": "en-GB-RyanNeural",
        "ha": "ha-NG-MuhammedNeural",
        "yo": "yo-NG-AbimbolaNeural",
        "ig": "ig-NG-ChidinmaNeural",
    }
    voice = voices.get(language, "en-GB-SoniaNeural")

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
