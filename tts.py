"""Natural narration with Gemini TTS and an Edge Neural voice fallback."""
import asyncio
import base64
import json
import os

import edge_tts
import requests
import config


API_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
TIMEOUT_SECONDS = 300


def _profile_for_voice(voice):
    for profile in getattr(config, "LANGUAGES", {}).values():
        if profile.get("voice") == voice:
            return profile
    return {}


def _gemini_voiceover(text, out_path, voice, style):
    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing")
    response = requests.post(
        API_URL,
        headers={"x-goog-api-key": config.GEMINI_API_KEY},
        json={
            "model": getattr(config, "GEMINI_TTS_MODEL", "gemini-3.8-flash-tts"),
            "input": [{
                "type": "user_input",
                "content": [{
                    "type": "text",
                    "text": text,
                    "annotations": [{"type": "speech_metadata", "style": style}],
                }],
            }],
            "response_format": {"type": "audio"},
            "generation_config": {"speech_config": [{"voice": voice}]},
        },
        timeout=TIMEOUT_SECONDS,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Gemini TTS HTTP {response.status_code}: {response.text[:300]}")
    payload = response.json()
    audio_b64 = payload.get("output_audio", {}).get("data")
    if not audio_b64:
        for step in payload.get("steps", []):
            for item in step.get("content", []):
                if item.get("type") == "audio" and item.get("data"):
                    audio_b64 = item["data"]
    if not audio_b64:
        raise RuntimeError("Gemini TTS response did not contain audio")

    wav_path = os.path.splitext(out_path)[0] + ".gemini.wav"
    with open(wav_path, "wb") as audio_file:
        audio_file.write(base64.b64decode(audio_b64, validate=True))
    if os.path.getsize(wav_path) < 128:
        raise RuntimeError("Gemini TTS returned an empty audio file")
    return wav_path


async def _edge_speak(text, out_path, voice, rate):
    await edge_tts.Communicate(text, voice=voice, rate=rate).save(out_path)


def make_voiceover(text: str, out_path: str, voice: str = None,
                   rate: str = None) -> str:
    if not text or not text.strip():
        raise ValueError("Cannot synthesize an empty narration")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    profile = _profile_for_voice(voice)
    gemini_voice = profile.get("gemini_voice") or getattr(
        config, "GEMINI_TTS_VOICE", "Charon"
    )
    style = profile.get("tts_style") or getattr(
        config, "GEMINI_TTS_STYLE", "Natural, conversational narration with clear pronunciation and a relaxed pace."
    )
    gemini_error = None
    try:
        result = _gemini_voiceover(text, out_path, gemini_voice, style)
        print(f"  Natural Gemini TTS voice generated ({gemini_voice}).")
        return result
    except (requests.RequestException, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as error:
        gemini_error = error
        print(f"  Gemini TTS unavailable ({type(error).__name__}); trying Edge Neural.")

    edge_voice = profile.get("voice") or voice or getattr(config, "VOICE", "en-US-GuyNeural")
    edge_rate = rate or profile.get("rate") or getattr(config, "VOICE_RATE", "+0%")
    edge_path = os.path.splitext(out_path)[0] + ".edge.mp3"
    try:
        asyncio.run(asyncio.wait_for(
            _edge_speak(text, edge_path, edge_voice, edge_rate), timeout=TIMEOUT_SECONDS
        ))
        if not os.path.isfile(edge_path) or os.path.getsize(edge_path) < 128:
            raise RuntimeError("Edge TTS returned an empty audio file")
        print(f"  Edge Neural voice generated ({edge_voice}).")
        return edge_path
    except Exception as edge_error:
        raise RuntimeError(
            "Both Gemini TTS and Edge Neural failed; skipping robotic offline speech. "
            f"Gemini: {type(gemini_error).__name__}; Edge: {type(edge_error).__name__}"
        ) from edge_error
