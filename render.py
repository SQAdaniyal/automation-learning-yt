"""
Render: clips + voice + music + hook text overlay + subscribe bar.
NO title text box — sirf shocking hook (pehle 4 sec) dikhega.
"""
import os
import glob
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    VideoFileClip, AudioFileClip, ImageClip,
    CompositeVideoClip, CompositeAudioClip,
    concatenate_videoclips, concatenate_audioclips,
)
import config

CHANNEL_NAME = "NeuralEdge"
MUSIC_VOLUME = 0.10

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _font(size: int):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _background_music(total: float):
    files = glob.glob("music/*.mp3") + glob.glob("music/*.wav")
    if not files:
        return None
    try:
        path = random.choice(files)
        m = AudioFileClip(path)
        if m.duration < total:
            clips = [AudioFileClip(path) for _ in range(int(total / m.duration) + 2)]
            m.close()
            m = concatenate_audioclips(clips)
        return m.subclipped(0, total).with_volume_scaled(MUSIC_VOLUME)
    except Exception as e:
        print(f"  Music skip: {e}")
        return None


def _hook_overlay(hook_text: str, res: tuple, duration: float) -> ImageClip:
    w, h = res
    is_short = h > w

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    fsize = int(w * 0.072) if not is_short else int(w * 0.055)
    font = _font(fsize)

    words = hook_text.split()
    lines, line = [], ""
    max_w = w * 0.88
    for word in words:
        test = (line + " " + word).strip()
        if draw.textlength(test, font=font) < max_w:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    lines = lines[:4]

    line_h = int(fsize * 1.25)
    box_h = line_h * len(lines) + 60
    y_pos = int(h * 0.30) if is_short else int(h * 0.20)

    draw.rectangle([(0, y_pos - 20), (w, y_pos + box_h)], fill=(0, 0, 0, 185))
    draw.rectangle([(0, y_pos - 20), (10, y_pos + box_h)], fill=(0, 200, 255, 255))

    for i, ln in enumerate(lines):
        lw = draw.textlength(ln, font=font)
        x = (w - lw) / 2
        y = y_pos + 10 + i * line_h
        draw.text((x + 3, y + 3), ln, font=font, fill=(0, 0, 0, 180))
        draw.text((x, y), ln, font=font, fill=(255, 255, 255, 255))

    show = min(4.0, duration - 0.5)
    return ImageClip(np.array(img)).with_duration(show).with_position((0, 0))


def _subscribe_bar(res: tuple) -> Image.Image:
    w, h = res
    bar_w, bar_h = int(w * 0.60), int(w * 0.082)
    img = Image.new("RGBA", (bar_w, bar_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([(0, 0), (bar_w, bar_h)], radius=bar_h // 2,
                        fill=(20, 20, 20, 210))
    pad = int(bar_h * 0.20)
    bx0, by0 = pad, pad
    bsz = bar_h - 2 * pad
    d.pieslice([bx0, by0, bx0 + bsz, by0 + int(bsz * 1.1)], 180, 360,
               fill=(0, 200, 255, 255))
    d.rectangle([bx0, by0 + bsz // 2, bx0 + bsz, by0 + int(bsz * 0.78)],
                fill=(0, 200, 255, 255))
    d.ellipse([bx0 + bsz // 2 - bsz // 8, by0 + int(bsz * 0.74),
               bx0 + bsz // 2 + bsz // 8, by0 + int(bsz * 0.74) + bsz // 4],
              fill=(0, 200, 255, 255))
    f_btn = _font(int(bar_h * 0.34))
    btn_text = "SUBSCRIBE"
    btn_tw = d.textlength(btn_text, font=f_btn)
    btn_x0 = bx0 + bsz + pad
    btn_w = int(btn_tw + pad * 2)
    d.rounded_rectangle([(btn_x0, pad), (btn_x0 + btn_w, bar_h - pad)],
                        radius=(bar_h - 2 * pad) // 2, fill=(230, 33, 23, 255))
    d.text((btn_x0 + pad, (bar_h - f_btn.size) // 2 - 2), btn_text,
           font=f_btn, fill=(255, 255, 255, 255))
    f_name = _font(int(bar_h * 0.30))
    name_x = btn_x0 + btn_w + pad
    d.text((name_x, (bar_h - f_name.size) // 2 - 2), CHANNEL_NAME,
           font=f_name, fill=(255, 255, 255, 255))
    used_w = int(name_x + d.textlength(CHANNEL_NAME, font=f_name) + pad)
    return img.crop((0, 0, min(used_w, bar_w), bar_h))


def _subscribe_clips(res: tuple, total: float) -> list:
    w, h = res
    bar = np.array(_subscribe_bar(res))
    y = int(h * 0.84) if h > w else int(h * 0.65)
    clips = []
    starts = [5.0]
    if total > 18:
        starts.append(max(6.5, total - 6.5))
    for st in starts:
        if st + 1 < total:
            clips.append(
                ImageClip(bar)
                .with_duration(min(4.0, total - st - 0.3))
                .with_start(st)
                .with_position(("center", y))
            )
    return clips


def _fit(clip: VideoFileClip, res: tuple) -> VideoFileClip:
    tw, th = res
    ratio = clip.w / clip.h
    target = tw / th
    if ratio > target:
        clip = clip.resized(height=th)
        x1 = (clip.w - tw) / 2
        clip = clip.cropped(x1=x1, x2=x1 + tw)
    else:
        clip = clip.resized(width=tw)
        y1 = (clip.h - th) / 2
        clip = clip.cropped(y1=y1, y2=y1 + th)
    return clip


def render_video(clip_paths: list, audio_path: str, title: str,
                 kind: str, out_path: str, hook_text: str = "") -> str:
    res = config.LONG_RESOLUTION if kind == "long" else config.SHORT_RESOLUTION
    voice = AudioFileClip(audio_path)
    total = voice.duration + 0.5

    segments, t, i, opened = [], 0.0, 0, []
    while t < total and clip_paths:
        path = clip_paths[i % len(clip_paths)]
        try:
            c = VideoFileClip(path)
            opened.append(c)
            seg_len = min(c.duration, 6.0, total - t)
            if seg_len < 1:
                seg_len = total - t
            seg = _fit(c.subclipped(0, min(seg_len, c.duration)), res)
            segments.append(seg)
            t += seg.duration
        except Exception as e:
            print(f"  Clip skip: {e}")
            if path in clip_paths:
                clip_paths.remove(path)
            continue
        i += 1

    if not segments:
        raise RuntimeError("No usable clips found")

    music = _background_music(total)
    audio = CompositeAudioClip([voice, music]) if music else voice

    video = concatenate_videoclips(segments).with_duration(total)

    overlays = []
    if hook_text and total > 2 and kind == "short":
        overlays.append(_hook_overlay(hook_text, res, total))
    overlays += _subscribe_clips(res, total)

    final = CompositeVideoClip([video] + overlays, size=res).with_audio(audio)
    final.write_videofile(
        out_path, fps=config.FPS, codec="libx264", audio_codec="aac",
        preset="faster", threads=4, logger=None,
    )
    for c in opened:
        c.close()
    voice.close()
    return out_path
