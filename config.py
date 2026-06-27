"""
NeuralEdge settings — AI/Tech facts (English only).
"""
import os

# ---------- API KEYS ----------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
YT_CLIENT_ID = os.environ.get("YT_CLIENT_ID", "")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET", "")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN", "")

# ---------- CONTENT ----------
NICHE = "AI tools and breakthroughs, future technology shock facts, AI vs human comparisons, mind-bending tech statistics, what AI can do now that seems impossible, future predictions backed by real trends"
LONG_VIDEOS_PER_DAY = 1
SHORTS_PER_DAY = 5

# ---------- LANGUAGES ----------
LANGUAGES = {
    "English": {"voice": "en-US-ChristopherNeural", "rate": "+15%", "code": "en"},
}

# ---------- VIDEO ----------
LONG_TARGET_WORDS = 500
SHORT_TARGET_WORDS = 55
LONG_RESOLUTION = (1920, 1080)
SHORT_RESOLUTION = (1080, 1920)
FPS = 24

# ---------- UPLOAD ----------
UPLOAD_TO_YOUTUBE = True
PRIVACY_STATUS = "public"
CATEGORY_ID = "28"

# ---------- MODELS ----------
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

# ---------- PATHS ----------
WORK_DIR = "output"
USED_TOPICS_FILE = "used_topics.json"
