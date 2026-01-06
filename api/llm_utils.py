import aiohttp
import os
import json

async def call_gemini(prompt: str, api_key: str):
    """Generic function to call Gemini API"""
    if not api_key: return None

    model_name = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers={"Content-Type": "application/json"}) as response:
                if response.status != 200:
                    print(f"Gemini Error {response.status}: {await response.text()}")
                    return None
                data = await response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Gemini Exception: {e}")
        return None

async def translate_text(text_list: list, api_key: str) -> list:
    """
    Translate a list of strings to Traditional Chinese.
    Returns a list of same length.
    """
    if not text_list: return []

    # Simple batching
    prompt = "請將以下每一行英文標題翻譯成繁體中文，保持原意，不要加額外的編號或解釋，每一行對應一行翻譯：\n\n"
    prompt += "\n".join(text_list)

    result = await call_gemini(prompt, api_key)

    if result:
        # Split by newline and clean
        translated = [line.strip() for line in result.strip().split('\n') if line.strip()]
        # Safety check: if length mismatch, return original (or partial)
        if len(translated) == len(text_list):
            return translated
        else:
            print(f"Translation count mismatch: Input {len(text_list)} vs Output {len(translated)}")
            # Fallback: return original if simple mismatch, or try to align?
            # Safer to return original to avoid wrong mapping
            return text_list

    return text_list
