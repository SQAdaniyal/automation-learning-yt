"""
YouTube upload + auto-comment — NeuralEdge (Urdu + English mix).
"""
import os
import random
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import config

COMMENTS_EN = [
    "Did this fact surprise you? Let us know! 👇",
    "What AI breakthrough should we cover next? 🤖",
    "Share this with someone who loves tech! 🔥",
    "Follow for daily AI facts that will blow your mind! 🔔",
    "Is this exciting or scary to you? Let's discuss 👇",
]

COMMENTS_UR = [
    "Kya yeh fact aapko hairan kar gaya? Neeche batayein! 👇",
    "Agli AI video kis topic par banayen? 🤖",
    "Apne dost ko share karein jo tech pasand karta ho! 🔥",
    "Roz AI facts ke liye Follow karein! 🔔",
    "Yeh exciting lagta hai ya scary? Comment karein 👇",
]


def _youtube():
    creds = Credentials(
        None,
        refresh_token=config.YT_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=config.YT_CLIENT_ID,
        client_secret=config.YT_CLIENT_SECRET,
    )
    return build("youtube", "v3", credentials=creds)


def _upload_thumbnail(yt, video_id: str, thumb_path: str):
    try:
        yt.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumb_path, mimetype="image/jpeg")
        ).execute()
        print("  🖼️ Thumbnail uploaded")
    except Exception as e:
        print(f"  Thumbnail skip: {e}")


def _post_comment(yt, video_id: str, lang_code: str = "en"):
    try:
        pool = COMMENTS_UR if lang_code == "ur" else COMMENTS_EN
        yt.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {"textOriginal": random.choice(pool)}
                    },
                }
            },
        ).execute()
        print("  💬 Auto-comment posted")
    except Exception as e:
        print(f"  Comment skip: {e}")


def upload_video(path: str, title: str, description: str,
                 tags: list, thumb_path: str = None,
                 lang_code: str = "en") -> str:
    yt = _youtube()
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:4900],
            "tags": tags[:30],
            "categoryId": config.CATEGORY_ID,
            "defaultLanguage": lang_code,
            "defaultAudioLanguage": lang_code,
        },
        "status": {
            "privacyStatus": config.PRIVACY_STATUS,
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(path, chunksize=8 * 1024 * 1024, resumable=True)
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Upload: {int(status.progress() * 100)}%")
    video_id = response["id"]
    print(f"  ✅ Uploaded: https://youtu.be/{video_id}")
    if thumb_path and os.path.exists(thumb_path):
        _upload_thumbnail(yt, video_id, thumb_path)
    _post_comment(yt, video_id, lang_code)
    return video_id
