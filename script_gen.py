"""
Gemini API — NeuralEdge AI/Tech viral scripts. Urdu + English mix.
"""
import json
import re
import time
import requests
import config

MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite"]
BASE = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"

VIRAL_CATEGORIES = """
- AI tools that can now do things that seemed impossible 2 years ago
- Shocking AI vs Human comparisons (speed, accuracy, creativity)
- Scary-smart AI predictions that came true
- Mind-bending tech statistics (computing power comparisons across eras)
- Jobs/industries AI is already quietly replacing
- Future tech predictions backed by real current trends
- AI capabilities most people don't know exist yet
- Tech history ironies that sound fake but are true
"""

TITLE_FORMULAS_EN = """
- "This AI Tool Just Did What Took Humans [X] Years"
- "99% of People Don't Know AI Can Already Do This"
- "Your Phone Has More Power Than [shocking historical comparison]"
- "Scientists Are Stunned By What This AI Just Did"
- "By 2030, AI Will [specific bold prediction]"
- "The Scary Reason AI Companies Don't Talk About [topic]"
- "[Number] AI Facts That Will Change How You See Technology"
"""

TITLE_FORMULAS_UR = """
- "AI Ab Yeh Kar Sakta Hai Jo Pehle Sirf Insaan Karte Thay"
- "99% Log Nahi Jantay AI Pehle Se Yeh Kar Raha Hai"
- "Yeh AI Fact Aapko Raat Ko Neend Nahi Aane Dega"
- "[Number] AI Secrets Jo Aapko Zaroor Janne Chahiye"
- "AI Ne [topic] Mein Insaan Ko Peeche Chhod Diya"
"""


def _ask_gemini(prompt: str) -> str:
    for model in MODELS:
        for attempt in range(4):
            try:
                r = requests.post(
                    BASE.format(m=model),
                    params={"key": config.GEMINI_API_KEY},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.9},
                    },
                    timeout=90,
                )
                if r.status_code == 200:
                    return r.json()["candidates"][0]["content"]["parts"][0]["text"]
                print(f"  [{model}] HTTP {r.status_code}: {r.text[:200]}", flush=True)
                if r.status_code in (429, 503):
                    time.sleep(25 * (attempt + 1))
                    continue
                break
            except Exception as e:
                print(f"  [{model}] error (attempt {attempt+1}): {e}", flush=True)
                time.sleep(10)
        print(f"  [{model}] fail — next model...", flush=True)
    raise RuntimeError("Gemini API failed (all models tried)")


def _parse_json(text: str):
    text = re.sub(r"```json|```", "", text).strip()
    dec = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch in "[{":
            try:
                obj, _ = dec.raw_decode(text[i:])
                return obj
            except json.JSONDecodeError:
                continue
    raise ValueError("No valid JSON: " + text[:120])


def generate_topics(count: int, kind: str, used: list) -> list:
    style = (
        "3-4 minute AI/tech facts video"
        if kind == "long"
        else "20-25 second viral YouTube Short (ONE shocking AI/tech fact)"
    )
    prompt = f"""You are a viral tech YouTube strategist for a worldwide AI/future-tech facts channel.

Generate exactly {count} FRESH topics for a {style}.

Pick ONLY from these categories:
{VIRAL_CATEGORIES}

RULES:
- Every topic must trigger "wait, WHAT?!" — genuinely surprising
- All facts must be 100% TRUE, current, and verifiable
- Visually supportable by stock footage (technology, computers, robots, labs)
- AVOID these already-used topics: {json.dumps(used[-150:], ensure_ascii=False)}
- For Shorts: ONE singular shocking fact, not a list
- Must be understandable to a general (non-technical) audience

Respond ONLY with a JSON array of strings. No other text."""
    return _parse_json(_ask_gemini(prompt))[:count]


def generate_script(topic: str, kind: str, language: str = "English") -> dict:
    is_urdu = language == "Urdu"

    if is_urdu:
        lang_instruction = """LANGUAGE: Natural spoken URDU (Urdu script). Simple everyday words, energetic tone. English tech terms, numbers, and AI names are OK as-is."""
        title_formulas = TITLE_FORMULAS_UR
        title_lang = "Roman Urdu"
        follow_cta = "Roz AI facts ke liye Follow karein!"
        subscribe_cta = "Subscribe karein aur daily AI breakthroughs ke liye bell dabayein! 🔔"
        hashtags = "#AI #ArtificialIntelligence #TechNews #Urdu #UrduFacts #FutureTech #Shorts #NeuralEdge #Technology #Innovation"
    else:
        lang_instruction = """LANGUAGE: Natural spoken ENGLISH, confident and energetic but credible tone."""
        title_formulas = TITLE_FORMULAS_EN
        title_lang = "English"
        follow_cta = "Follow for daily AI facts that will blow your mind!"
        subscribe_cta = "Subscribe for daily AI breakthroughs! 🔔"
        hashtags = "#AI #ArtificialIntelligence #TechNews #FutureTech #MindBlowing #Innovation #TechFacts #Shorts #NeuralEdge #DidYouKnow"

    if kind == "short":
        structure = f"""
SHORTS RULES:
- Line 1 = Immediate shock fact drop. No greeting, no "did you know".
- Lines 2-3 = Why this matters, in simple words
- Last line = "{follow_cta}"
- Under 55 words total."""
    else:
        structure = f"""
LONG VIDEO RULES:
- Open with the single most shocking fact — no intro, no greeting
- Build through 5-7 facts, each topping the last
- Use "but here's where it gets scary..." transitions
- End with most mind-blowing fact + "{subscribe_cta}"
- ~400 words, energetic but credible"""

    prompt = f"""Write a YouTube {'Short' if kind == 'short' else 'video'} script for: "{topic}"

{structure}
{lang_instruction}

DELIVER a JSON object with these exact keys:

"hook_text": MAX 7 WORDS in ENGLISH (for ON-SCREEN display, ALL CAPS, works without sound). Example: "AI BEAT DOCTORS AT CANCER DETECTION"

"script": Full voiceover script in {language}. No emojis, no stage directions.

"title": High-CTR title in {title_lang} using one of:
{title_formulas}
Under 90 characters. {"End with ' #Shorts'" if kind == 'short' else ""}

"description": Line 1 = hook. Line 2 = "{subscribe_cta}". Line 3 = 12 hashtags: {hashtags} + 2 topic-specific tags.

"tags": 15 SEO English tags mixing broad and specific keywords.

"keywords": 5 simple English words for stock footage (e.g. "robot", "data center", "circuit board").

COMPLIANCE: All facts 100% true. No sci-fi speculation as fact. Title must match content.

Respond ONLY with the JSON object. No other text."""

    data = _parse_json(_ask_gemini(prompt))
    data["topic"] = topic
    data["kind"] = kind
    data["language"] = language
    if "hook_text" not in data:
        data["hook_text"] = topic.upper()[:40]
    return data
