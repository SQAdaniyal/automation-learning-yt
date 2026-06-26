"""
Main pipeline — NeuralEdge daily automation (Urdu + English random mix).
"""
import json
import os
import random
import shutil
import traceback

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


def make_one(topic: str, kind: str, idx: int) -> bool:
    workdir = os.path.join(config.WORK_DIR, f"{kind}_{idx}")
    os.makedirs(workdir, exist_ok=True)
    try:
        language = random.choice(list(config.LANGUAGES.keys()))
        lang_cfg = config.LANGUAGES[language]
        print(f"\n=== [{kind} #{idx}] ({language}) {topic} ===")

        print("1) Script generate ho raha hai...")
        pkg = script_gen.generate_script(topic, kind, language)
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
            upload.upload_video(
                out, pkg["title"], desc,
                pkg.get("tags", []),
                thumb_path=thumb,
                lang_code=lang_cfg["code"]
            )
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
    ok = fail = 0

    print("Aaj ke topics generate ho rahe hain...")
    long_topics = script_gen.generate_topics(
        config.LONG_VIDEOS_PER_DAY, "long", used)
    short_topics = script_gen.generate_topics(
        config.SHORTS_PER_DAY, "short", used)
    print("Long :", long_topics)
    print("Short:", short_topics)

    for i, t in enumerate(long_topics, 1):
        if make_one(t, "long", i):
            ok += 1
            used.append(t)
        else:
            fail += 1
        save_used(used)

    for i, t in enumerate(short_topics, 1):
        if make_one(t, "short", i):
            ok += 1
            used.append(t)
        else:
            fail += 1
        save_used(used)

    print(f"\n===== DONE: {ok} success, {fail} fail =====")
    if ok == 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
