#!/usr/bin/env python3
"""
Transcriptor (Windows)
By the BGGG — Background Gremlin Group

Pulls FULL YouTube transcripts (captions) and exports them as:
- timestamps (.txt)
- line-by-line (.txt)
- paragraph formatted (.txt)

Windows-friendly long output viewing using pager (more).
No YouTube API key needed.

Install:
  py -m pip install youtube-transcript-api
"""

import os
import re
import sys
import json
import shutil
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime

from youtube_transcript_api import YouTubeTranscriptApi


APP_NAME = "Transcriptor"
AUTHOR = "BGGG — Background Gremlin Group"

BANNER = r"""
 _______                                  _      _
|__   __|                                | |    | |
   | |_ __ __ _ _ __  ___  ___ _ __ _ ___| |__  | |_ ___  _ __
   | | '__/ _` | '_ \/ __|/ __| '__| '_ \ | '_ \ | __/ _ \| '__|
   | | | | (_| | | | \__ \ (__| |  | |_) || | | || || (_) | |
   |_|_|  \__,_|_| |_|___/\___|_|  | .__/ |_| |_| \__\___/|_|
                                   | |
                                   |_|

Transcriptor (Windows) — Developed by the BGGG (Background Gremlin Group)
"""

MENU = """
[1] Pull transcript WITH timestamps (show + optional save)
[2] Pull transcript WITHOUT timestamps (line-by-line) (show + optional save)
[3] Pull transcript WITHOUT timestamps (paragraphs) (show + optional save)
[4] Pull & SAVE ALL (timestamps + lines + paragraphs)
[5] Help
[6] Exit
"""

HELP_TEXT = """
How it works
- Transcriptor pulls YouTube captions using youtube-transcript-api.
- Many videos have multiple caption tracks (MANUAL vs AUTO and multiple languages).
  Pick the track that matches what you see on YouTube.

Long transcripts
- Windows terminals can feel "cut off" due to scrollback limits.
- Use the pager prompt (more) to scroll the FULL output.

Output folder
- By default: .\\Transcripts (next to this script)
"""

VIDEO_ID_RE = re.compile(
    r"(?:v=|youtu\.be/|youtube\.com/(?:embed/|watch\?v=|shorts/))([A-Za-z0-9_-]{11})"
)


# -----------------------------
# Console helpers
# -----------------------------
def clear():
    os.system("cls" if os.name == "nt" else "clear")


def ask_yes_no(prompt: str, default_yes: bool = True) -> bool:
    d = "y" if default_yes else "n"
    ans = input(f"{prompt} (y/n) [default {d}]: ").strip().lower()
    if not ans:
        return default_yes
    return ans.startswith("y")


def show_full_text(text: str, use_pager: bool = True):
    """
    Use Windows pager "more" to reliably view long output.
    """
    if use_pager:
        try:
            # 'more' is a shell built-in; invoke via cmd
            p = subprocess.Popen(["cmd", "/c", "more"], stdin=subprocess.PIPE, text=True)
            p.communicate(text)
            return
        except Exception:
            pass
    print(text)


# -----------------------------
# Filesystem helpers
# -----------------------------
def ensure_out_dir() -> str:
    base = os.path.join(os.getcwd(), "Transcripts")
    os.makedirs(base, exist_ok=True)
    return base


def safe_filename(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[^\w\-. ]+", "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name or "transcript"


def save_text(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# -----------------------------
# YouTube helpers
# -----------------------------
def extract_video_id(s: str) -> str:
    s = s.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", s):
        return s
    m = VIDEO_ID_RE.search(s)
    if m:
        return m.group(1)
    raise ValueError("Could not find a valid 11-character YouTube video ID in that input.")


def fetch_oembed_metadata(video_id: str) -> dict:
    """
    Title + channel without API key.
    If it fails (network restrictions), tool still works (falls back to Unknown).
    """
    url = f"https://youtu.be/{video_id}"
    oembed = "https://www.youtube.com/oembed?" + urllib.parse.urlencode(
        {"url": url, "format": "json"}
    )
    try:
        req = urllib.request.Request(oembed, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        return {
            "title": (data.get("title") or "").strip(),
            "channel": (data.get("author_name") or "").strip(),
            "url": url,
        }
    except Exception:
        return {"title": "", "channel": "", "url": url}


def make_header(meta: dict) -> str:
    title = meta.get("title") or "Unknown Title"
    channel = meta.get("channel") or "Unknown Channel"
    url = meta.get("url") or ""
    return (
        f"{APP_NAME}\n"
        f"Developed by the BGGG (Background Gremlin Group)\n"
        f"Title: {title}\n"
        f"Channel: {channel}\n"
        f"Video: {url}\n"
        + "-" * 70
        + "\n"
    )


# -----------------------------
# Transcript fetch (robust + version-proof)
# -----------------------------
def normalize_entry(e) -> dict:
    """
    youtube-transcript-api may return dict entries or snippet objects.
    Normalize to dict with text/start/duration.
    """
    if isinstance(e, dict):
        return {
            "text": e.get("text", "") or "",
            "start": float(e.get("start", 0.0) or 0.0),
            "duration": float(e.get("duration", 0.0) or 0.0),
        }
    text = getattr(e, "text", "") or ""
    start = getattr(e, "start", 0.0)
    duration = getattr(e, "duration", 0.0)
    try:
        start = float(start or 0.0)
    except Exception:
        start = 0.0
    try:
        duration = float(duration or 0.0)
    except Exception:
        duration = 0.0
    return {"text": text, "start": start, "duration": duration}


def normalize_entries(entries):
    return [normalize_entry(x) for x in entries]


def list_tracks(video_id: str):
    tl = YouTubeTranscriptApi.list_transcripts(video_id)
    return [t for t in tl]


def describe_track(t) -> str:
    kind = "AUTO" if getattr(t, "is_generated", False) else "MANUAL"
    return f"{t.language} ({t.language_code}) - {kind}"


def pick_track_interactive(tracks):
    print("\nAvailable transcript tracks:\n")
    for i, t in enumerate(tracks, start=1):
        print(f"  [{i}] {describe_track(t)}")

    sel = input("\nChoose a track number [default 1]: ").strip()
    if not sel:
        return tracks[0]
    try:
        idx = int(sel)
        if 1 <= idx <= len(tracks):
            return tracks[idx - 1]
    except ValueError:
        pass
    print("\nInvalid selection. Using default (1).")
    return tracks[0]


def pick_track_fullest(tracks):
    """
    Optional helper: automatically choose the 'fullest' track by fetching each
    and choosing the one with the most entries.

    This can take longer on videos with many tracks, but helps when one track is
    abridged. User can still choose interactive mode.
    """
    best = None
    best_len = -1
    for t in tracks:
        try:
            entries = t.fetch()
            n = len(entries) if entries is not None else 0
            if n > best_len:
                best_len = n
                best = t
        except Exception:
            continue
    return best if best is not None else tracks[0]


def fetch_full_entries(video_id: str):
    tracks = list_tracks(video_id)
    if not tracks:
        raise RuntimeError("No transcripts available for this video.")

    print("\nTrack selection:\n  [1] Choose manually (recommended)\n  [2] Auto-pick the fullest track (may take longer)")
    mode = input("Select [default 1]: ").strip() or "1"

    if mode == "2":
        chosen = pick_track_fullest(tracks)
        print(f"\nAuto-picked: {describe_track(chosen)}\n")
    else:
        chosen = pick_track_interactive(tracks)

    # Fetch chosen track
    try:
        entries = chosen.fetch()
        return normalize_entries(entries)
    except Exception as e1:
        # fallback: direct get_transcript (usually default language)
        try:
            return normalize_entries(YouTubeTranscriptApi.get_transcript(video_id))
        except Exception as e2:
            raise RuntimeError(f"Failed to fetch transcript.\n- Track fetch error: {e1}\n- Fallback error: {e2}")


# -----------------------------
# Formatting
# -----------------------------
def format_with_timestamps(entries) -> str:
    out = []
    for e in entries:
        text = (e["text"] or "").replace("\n", " ").strip()
        if not text:
            continue
        out.append(f"[{e['start']:.2f}s] {text}")
    return "\n".join(out).strip() + "\n"


def format_line_by_line(entries) -> str:
    out = []
    for e in entries:
        text = (e["text"] or "").replace("\n", " ").strip()
        if text:
            out.append(text)
    return "\n".join(out).strip() + "\n"


def format_paragraphs(entries, gap_seconds: float = 1.25) -> str:
    paras = []
    cur = []
    prev_start = None

    for e in entries:
        start = float(e["start"])
        text = (e["text"] or "").replace("\n", " ").strip()
        if not text:
            continue

        if prev_start is None:
            cur.append(text)
        else:
            if (start - prev_start) > gap_seconds:
                paras.append(" ".join(cur).strip())
                cur = [text]
            else:
                cur.append(text)

        prev_start = start

    if cur:
        paras.append(" ".join(cur).strip())

    return "\n\n".join(p for p in paras if p).strip() + "\n"


# -----------------------------
# Save helpers
# -----------------------------
def default_base(meta: dict, video_id: str) -> str:
    title = (meta.get("title") or "").strip()
    if title:
        return safe_filename(f"{title} - {video_id}")
    return safe_filename(video_id)


def save_as_prompt(base_default: str, suffix: str, content: str):
    out_dir = ensure_out_dir()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_name = f"{base_default}_{stamp}{suffix}.txt"

    if not ask_yes_no("Save to .\\Transcripts ?", default_yes=True):
        return None

    name = input(f"Filename [default: {default_name}]: ").strip()
    if not name:
        name = default_name
    if not name.lower().endswith(".txt"):
        name += ".txt"

    path = os.path.join(out_dir, safe_filename(name))
    save_text(path, content)
    return path


def save_all(base_default: str, header: str, ts: str, lines: str, paras: str):
    out_dir = ensure_out_dir()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    p1 = os.path.join(out_dir, f"{base_default}_{stamp}_timestamps.txt")
    p2 = os.path.join(out_dir, f"{base_default}_{stamp}_lines.txt")
    p3 = os.path.join(out_dir, f"{base_default}_{stamp}_paragraphs.txt")

    save_text(p1, header + ts)
    save_text(p2, header + lines)
    save_text(p3, header + paras)

    return [p1, p2, p3]


# -----------------------------
# Main actions
# -----------------------------
def get_video_and_entries():
    url = input("Enter YouTube video URL or ID: ").strip()
    video_id = extract_video_id(url)
    meta = fetch_oembed_metadata(video_id)
    entries = fetch_full_entries(video_id)
    if not entries:
        raise RuntimeError("Transcript fetch returned 0 entries.")
    print(f"Fetched {len(entries)} transcript entries.\n")
    return video_id, meta, entries


def action_show_and_optional_save(mode: str):
    video_id, meta, entries = get_video_and_entries()
    header = make_header(meta)
    base = default_base(meta, video_id)

    if mode == "ts":
        body = format_with_timestamps(entries)
        title = "TRANSCRIPT WITH TIMESTAMPS"
        suffix = "_timestamps"
    elif mode == "lines":
        body = format_line_by_line(entries)
        title = "TRANSCRIPT (LINE BY LINE)"
        suffix = "_lines"
    else:
        gap = input("Paragraph gap seconds [default 1.25]: ").strip()
        try:
            gap_s = float(gap) if gap else 1.25
        except ValueError:
            gap_s = 1.25
        body = format_paragraphs(entries, gap_seconds=gap_s)
        title = f"TRANSCRIPT (PARAGRAPHS, gap>{gap_s}s)"
        suffix = "_paragraphs"

    full = header + body

    clear()
    print(BANNER)
    print(title)
    print("-" * 70)

    use_pager = ask_yes_no("View using pager (recommended for long transcripts)?", default_yes=True)
    show_full_text(full, use_pager=use_pager)

    path = save_as_prompt(base, suffix, full)
    if path:
        print(f"\nSaved: {path}\n")


def action_save_all():
    video_id, meta, entries = get_video_and_entries()
    header = make_header(meta)
    base = default_base(meta, video_id)

    ts = format_with_timestamps(entries)
    lines = format_line_by_line(entries)

    gap = input("Paragraph gap seconds [default 1.25]: ").strip()
    try:
        gap_s = float(gap) if gap else 1.25
    except ValueError:
        gap_s = 1.25
    paras = format_paragraphs(entries, gap_seconds=gap_s)

    if not ask_yes_no("Save ALL 3 formats to .\\Transcripts ?", default_yes=True):
        return

    paths = save_all(base, header, ts, lines, paras)
    print("\nSaved:")
    for p in paths:
        print(f" - {p}")
    print()


# -----------------------------
# Main loop
# -----------------------------
def main():
    while True:
        clear()
        print(BANNER)
        print(MENU)
        choice = input("Choose an option (1-6): ").strip()

        try:
            if choice == "1":
                action_show_and_optional_save("ts")
                input("Press Enter to return to menu...")
            elif choice == "2":
                action_show_and_optional_save("lines")
                input("Press Enter to return to menu...")
            elif choice == "3":
                action_show_and_optional_save("paras")
                input("Press Enter to return to menu...")
            elif choice == "4":
                action_save_all()
                input("Press Enter to return to menu...")
            elif choice == "5":
                clear()
                print(BANNER)
                print(HELP_TEXT)
                input("\nPress Enter to return to menu...")
            elif choice == "6":
                print("\nBye.\n")
                sys.exit(0)
            else:
                print("\nInvalid option. Pick 1-6.\n")
                input("Press Enter to try again...")
        except KeyboardInterrupt:
            print("\n\nCancelled.\n")
            input("Press Enter to return to menu...")
        except Exception as e:
            print(f"\nError: {e}\n")
            input("Press Enter to return to menu...")


if __name__ == "__main__":
    main()
