"""
Main pipeline — ScareWire daily automation (Urdu + English random mix).
"""
import json
import os
import random
import shutil
import traceback
from datetime import datetime, timedelta, timezone

import config
import script_gen
import tts
import footage
import render
import thumbnail

if config.UPLOAD_TO_YOUTUBE:
    import upload


def load_used() -> list:
    if os.path.exists(config.USED_TOPICS_FILE):
        with open(config.USED_TOPICS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_used(used: list):
    with open(config.USED_TOPICS_FILE, "w", encoding="utf-8") as f:
        json.dump(used, f, ensure_ascii=False, indent=1)


def load_video_history() -> list:
    if os.path.exists(config.VIDEO_HISTORY_FILE):
        try:
            with open(config.VIDEO_HISTORY_FILE, encoding="utf-8") as f:
                value = json.load(f)
                return value if isinstance(value, list) else []
        except (OSError, json.JSONDecodeError):
            print("  Upload history is unreadable; checking YouTube directly.")
    return []


def save_video_history(history: list):
    with open(config.VIDEO_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[-500:], f, ensure_ascii=False, indent=1)


def get_daily_upload_counts(history: list, recent_uploads: list, run_date) -> dict:
    uploads_by_id = {}
    for item in (recent_uploads or []) + (history or []):
        if not isinstance(item, dict):
            continue
        video_id = item.get("video_id")
        uploaded_at = item.get("uploaded_at")
        kind = item.get("kind")
        if (not video_id or not isinstance(uploaded_at, str)
                or kind not in {"long", "short"}):
            continue
        try:
            timestamp = datetime.fromisoformat(uploaded_at.replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            continue
        if (timestamp.astimezone(timezone.utc) + timedelta(hours=5)).date() == run_date:
            uploads_by_id[video_id] = kind
    counts = {"long": 0, "short": 0}
    for kind in uploads_by_id.values():
        counts[kind] += 1
    return counts


def validate_channel(channel_title: str):
    actual = "".join(channel_title.casefold().split())
    expected = "".join(config.CHANNEL_NAME.casefold().split())
    if actual != expected:
        raise RuntimeError(
            f"Authorized YouTube channel is {channel_title!r}; "
            f"expected {config.CHANNEL_NAME!r}. No videos were uploaded."
        )


def make_one(topic: str, kind: str, idx: int, video_history: list) -> bool:
    workdir = os.path.join(config.WORK_DIR, f"{kind}_{idx}")
    os.makedirs(workdir, exist_ok=True)
    try:
        language = random.choice(list(config.LANGUAGES.keys()))
        lang_cfg = config.LANGUAGES[language]
        print(f"\n=== [{kind} #{idx}] ({language}) {topic} ===")

        print("1) Script generate ho raha hai...")
        pkg = script_gen.generate_script(topic, kind, language)
        if kind == "short" and "#shorts" not in pkg["title"].lower():
            pkg["title"] = pkg["title"].rstrip() + " #Shorts"
        hook_text = pkg.get("hook_text", topic.upper()[:40])

        print("2) Voiceover ban raha hai...")
        audio = tts.make_voiceover(
            pkg["script"],
            os.path.join(workdir, "voice.mp3"),
            voice=lang_cfg["voice"],
            rate=lang_cfg["rate"]
        )

        print("3) Footage download ho rahi hai...")
        need = 10 if kind == "long" else 4
        clips = footage.download_clips(
            pkg["keywords"], kind, os.path.join(workdir, "clips"), need
        )
        if not clips:
            clips = footage.download_clips(
                ["technology", "computer", "futuristic"], kind,
                os.path.join(workdir, "clips"), need
            )
        if not clips:
            raise RuntimeError("Footage nahi mili")

        print("4) Video render ho rahi hai...")
        out = render.render_video(
            clips, audio, pkg["title"], kind,
            os.path.join(workdir, "final.mp4"),
            hook_text=hook_text
        )

        print("4b) Thumbnail ban raha hai...")
        thumb = thumbnail.make_thumbnail(
            pkg["title"], hook_text, kind,
            os.path.join(workdir, "thumb.jpg")
        )

        if config.UPLOAD_TO_YOUTUBE:
            print("5) YouTube par upload ho rahi hai...")
            desc = pkg["description"]
            if kind == "short" and "#shorts" not in desc.lower():
                desc += "\n#Shorts"
            video_id = upload.upload_video(
                out, pkg["title"], desc,
                pkg.get("tags", []),
                thumb_path=thumb,
                lang_code=lang_cfg["code"]
            )
            video_history.append({
                "video_id": video_id,
                "title": pkg["title"],
                "kind": kind,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            })
            save_video_history(video_history)
            shutil.rmtree(workdir, ignore_errors=True)
        else:
            print(f"  (Test mode) Video saved: {out}")
        return True

    except Exception:
        print(f"❌ FAIL [{kind} #{idx}]:")
        traceback.print_exc()
        return False


def main():
    os.makedirs(config.WORK_DIR, exist_ok=True)
    used = load_used()
    video_history = load_video_history()
    ok = fail = 0

    required = ["GEMINI_API_KEY", "PEXELS_API_KEY"]
    if config.UPLOAD_TO_YOUTUBE:
        required.extend(["YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"])
    missing = [name for name in required if not getattr(config, name)]
    if missing:
        raise RuntimeError("Missing required Actions secrets: " + ", ".join(missing))

    recent_uploads = []
    if config.UPLOAD_TO_YOUTUBE:
        try:
            channel_title, recent_uploads = upload.get_channel_identity_and_recent_uploads()
            validate_channel(channel_title)
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(
                f"Could not verify today's ScareWire uploads; a later recovery run will retry: {exc}"
            ) from exc
        local_date = (datetime.now(timezone.utc) + timedelta(hours=5)).date()
        counts = get_daily_upload_counts(video_history, recent_uploads, local_date)
        long_count = max(config.LONG_VIDEOS_PER_DAY - counts["long"], 0)
        short_count = max(config.SHORTS_PER_DAY - counts["short"], 0)
        if long_count + short_count == 0:
            print("Today's ScareWire upload target is already complete; skipping.")
            return
        print(f"Today's target remaining: {long_count} long, {short_count} Shorts.")
    else:
        long_count = config.LONG_VIDEOS_PER_DAY
        short_count = config.SHORTS_PER_DAY

    research = []
    try:
        with open(config.RESEARCH_NOTES_FILE, encoding="utf-8") as f:
            research = json.load(f)
        print(f"YouTube research notes loaded: {len(research)} video(s).")
    except (OSError, json.JSONDecodeError):
        pass
    print("Aaj ke topics generate ho rahe hain...")
    long_topics = script_gen.generate_topics(
        long_count, "long", used, research=research) if long_count else []
    short_topics = script_gen.generate_topics(
        short_count, "short", used, research=research) if short_count else []
    print("Long :", long_topics)
    print("Short:", short_topics)
    missing_topics = max(long_count - len(long_topics), 0) + max(
        short_count - len(short_topics), 0
    )
    if missing_topics:
        print(f"  Topic generation returned {missing_topics} fewer topic(s) than requested.")
        fail += missing_topics

    for i, t in enumerate(long_topics, 1):
        if make_one(t, "long", i, video_history):
            ok += 1
            used.append(t)
        else:
            fail += 1
        save_used(used)

    for i, t in enumerate(short_topics, 1):
        if make_one(t, "short", i, video_history):
            ok += 1
            used.append(t)
        else:
            fail += 1
        save_used(used)

    print(f"\n===== DONE: {ok} success, {fail} fail =====")
    if fail or ok == 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
