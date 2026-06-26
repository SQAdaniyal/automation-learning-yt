"""
Pexels API (free) se stock clips download karta hai.
"""
import os
import random
import requests
import config

API = "https://api.pexels.com/videos/search"


def _search(query: str, orientation: str, per_page: int = 12) -> list:
    try:
        r = requests.get(
            API,
            headers={"Authorization": config.PEXELS_API_KEY},
            params={
                "query": query,
                "orientation": orientation,
                "per_page": per_page,
                "size": "medium",
            },
            timeout=30,
        )
        r.raise_for_status()
        return r.json().get("videos", [])
    except Exception as e:
        print(f"  Pexels search error '{query}': {e}")
        return []


def _best_file(video: dict, min_w: int):
    files = sorted(
        [f for f in video.get("video_files", []) if f.get("width")],
        key=lambda f: f["width"],
    )
    for f in files:
        if f["width"] >= min_w:
            return f["link"]
    return files[-1]["link"] if files else None


def download_clips(keywords: list, kind: str, dest_dir: str, need: int = 8) -> list:
    os.makedirs(dest_dir, exist_ok=True)
    orientation = "landscape" if kind == "long" else "portrait"
    min_w = 1280 if kind == "long" else 700

    candidates = []
    for kw in keywords:
        for v in _search(kw, orientation):
            url = _best_file(v, min_w)
            dur = v.get("duration", 0)
            if url and 4 <= dur <= 60:
                candidates.append(url)

    random.shuffle(candidates)
    paths = []
    for i, url in enumerate(candidates):
        if len(paths) >= need:
            break
        path = os.path.join(dest_dir, f"clip_{i}.mp4")
        try:
            with requests.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(path, "wb") as f:
                    for chunk in r.iter_content(1024 * 512):
                        f.write(chunk)
            if os.path.getsize(path) > 100_000:
                paths.append(path)
        except Exception as e:
            print(f"  Download fail: {e}")
    return paths
