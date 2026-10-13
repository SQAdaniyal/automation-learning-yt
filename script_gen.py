"""
Gemini API — ScareWire factual AI/technology scripts. Urdu + English mix.
"""
import json
import re
import time
import requests
import config

MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite"]
BASE = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"

VIRAL_CATEGORIES = """
- Real deepfake and voice-cloning cases, with their limits explained
- Documented AI mistakes that affected people or organizations
- Privacy and surveillance technology used in daily life
- Genuine AI safety incidents and what investigators confirmed
- Technology history with a surprising, well-recorded explanation
- New AI capabilities demonstrated by named research or products
- Real security weaknesses and practical ways people can protect themselves
"""

TITLE_FORMULAS_EN = """
- "The Hidden Risk Behind [specific technology]"
- "What [specific AI system] Can Actually Do"
- "The Real Story Behind [verified AI event]"
- "How [specific technology] Can Affect Your Privacy"
- "The AI Feature With a Serious Limitation"
- "What Investigators Found About [verified incident]"
"""

TITLE_FORMULAS_UR = """
- "AI [specific kaam] asal mein kaise karta hai?"
- "[Technology] ka woh risk jo log aksar miss kar dete hain"
- "[Verified event] ke peeche asal mein kya hua?"
- "AI ki is capability ki ek aham limit hai"
- "Aapki privacy par [technology] ka kya asar ho sakta hai?"
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
                        "generationConfig": {"temperature": 0.7},
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
    prompt = f"""You are the ScareWire YouTube editor for unsettling, factual AI and technology stories.

Generate exactly {count} FRESH topics for a {style}.

Pick ONLY from these categories:
{VIRAL_CATEGORIES}

RULES:
- Make the viewer curious with one concrete, surprising, well-documented fact.
- Use claims supported by credible reporting, official records, or named research.
- Do not invent numbers, cases, quotes, expert reactions, or predictions.
- If a claim cannot be stated accurately with confidence, choose another topic.
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
        follow_cta = "ScareWire ko follow karein mazeed tech stories ke liye."
        subscribe_cta = "ScareWire ko subscribe karein mazeed factual tech stories ke liye."
        hashtags = "#AI #Technology #Deepfakes #Privacy #TechFacts #Urdu #UrduFacts #Shorts #ScareWire #DigitalSafety"
    else:
        lang_instruction = """LANGUAGE: Natural spoken ENGLISH, confident and energetic but credible tone."""
        title_formulas = TITLE_FORMULAS_EN
        title_lang = "English"
        follow_cta = "Follow ScareWire for unsettling, factual tech stories."
        subscribe_cta = "Subscribe to ScareWire for more factual technology stories."
        hashtags = "#AI #Technology #Deepfakes #Privacy #TechFacts #Shorts #ScareWire #DigitalSafety"

    if kind == "short":
        structure = f"""
SHORTS RULES:
- Line 1 = Immediate shock fact drop. No greeting, no "did you know".
- Explain why it matters in one clear line, without exaggeration
- Last line = "{follow_cta}"
- Under 55 words total."""
    else:
        structure = f"""
LONG VIDEO RULES:
- Open with the most concrete, verified detail; no greeting or filler
- Build one clear story with context, stakes, and a satisfying payoff
- Keep suspense through unanswered questions, then resolve them accurately
- Attribute named research or official findings when known; never invent a source
- End with the payoff and "{subscribe_cta}"
- ~400 words, engaging and credible"""

    prompt = f"""Write a YouTube {'Short' if kind == 'short' else 'video'} script for: "{topic}"

{structure}
{lang_instruction}

DELIVER a JSON object with these exact keys:

"hook_text": MAX 7 WORDS in ENGLISH (for ON-SCREEN display, ALL CAPS, works without sound). Use an accurate curiosity hook, not an unsupported claim.

"script": Full voiceover script in {language}. No emojis, no stage directions.

"title": High-CTR title in {title_lang} using one of:
{title_formulas}
Under 90 characters. {"End with ' #Shorts'" if kind == 'short' else ""}

"description": Line 1 = hook. Line 2 = "{subscribe_cta}". Line 3 = 12 hashtags: {hashtags} + 2 topic-specific tags.

"tags": 15 SEO English tags mixing broad and specific keywords.

"keywords": 5 simple English words for stock footage (e.g. "robot", "data center", "circuit board").

COMPLIANCE: Use only well-supported factual claims. Do not fabricate statistics, quotes, sources, or predictions. Clearly label uncertainty. If the supplied topic cannot be supported, narrow it to a defensible claim. Title must accurately match the script.

Respond ONLY with the JSON object. No other text."""

    data = _parse_json(_ask_gemini(prompt))
    data["topic"] = topic
    data["kind"] = kind
    data["language"] = language
    if "hook_text" not in data:
        data["hook_text"] = topic.upper()[:40]
    return data
