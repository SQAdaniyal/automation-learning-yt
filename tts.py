"""
edge-tts — voice/rate language ke hisaab se.
"""
import asyncio
import edge_tts
import config


async def _speak(text: str, out_path: str, voice: str, rate: str):
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(out_path)


def make_voiceover(text: str, out_path: str,
                   voice: str = None, rate: str = None) -> str:
    v = voice or config.LANGUAGES["English"]["voice"]
    r = rate or config.LANGUAGES["English"]["rate"]
    asyncio.run(_speak(text, out_path, v, r))
    return out_path
