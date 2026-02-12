#!/data/data/com.termux/files/usr/bin/env python3
"""
BGGG YouTube Transcriptor V2 (FULL transcript focus) — Termux / Android

Features
- Pulls FULL transcript from YouTube captions (when available)
- Language picker (manual/auto)
- Outputs:
  1) With timestamps (txt)
  2) Without timestamps (line-by-line) (txt)
  3) Without timestamps (paragraphs) (txt)
  4) Save ALL 3 formats
  5) Help
  6) Exit
- Ensures FULL output is shown (via built-in pager using 'less' if available)
- Ensures FULL output is saved to Android shared storage:
    ~/storage/shared/Transcripts

Setup (one time):
  pkg update -y
  pkg install -y python less
  pip install --upgrade pip
  pip install youtube-transcript-api
  termux-setup-storage
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


BANNER = r"""
___________                                          __         __                 
\__    ___/___________    ____   ______ ____ _______|__|_____ _/  |_  ____ _______ 
  |    |  \_  __ \__  \  /    \ /  ___// ___\\_  __ \  |____ \\   __\/ __ \\_  __ \
  |    |   |  | \// __ \_   |  \\___ \\  \___ |  | \/  |  |_\ \|  | (  \_\ )|  | \/
  |____|   |__|  (____  /___|  /____  \\___  /|__|  |__|   ___/|__|  \____/ |__|   
                      \/     \/     \/     \/          |__|                        
Developed by the BGGG
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
Notes about "FULL transcript"
- This tool pulls YouTube captions via youtube_transcript_api.
- If the transcript is very long, your terminal may not show all lines at once.
  To ensure you can VIEW everything, this program uses a pager ('less') when installed.
  Install: pkg install -y less
- Saved files always contain the FULL transcript content the API returns.

If a transcript seems "short"
- Pick a different language track (manual vs auto can differ).
- Some videos have multiple caption tracks; one may be abridged.
- If YouTube shows a transcript but the API fails, it can be due to restrictions.

Save location
- ~/storage/shared/Transcripts
- If saving fails: termux-setup-storage
"""


VIDEO_ID_RE = re.compile(
    r"(?:v=|youtu\.be/|youtube\.com/(?:embed/|watch\?v=|shorts/))([A-Za-z0-9_-]{11})"
)


# -----------------------------
# Basic utils
# -----------------------------
def clear():
    os.system("clear")


def safe_filename(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[^\w\-. ]+", "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name or "transcript"


def ensure_storage_dir() -> str:
    base = os.path.expanduser("~/storage/shared/Transcripts")
    os.makedirs(base, exist_ok=True)
    return base


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
    Can fail on some networks; program still works.
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
        "Developed by the BGGG\n"
        f"Title: {title}\n"
        f"Channel: {channel}\n"
        f"Video: {url}\n"
        + "-" * 70
        + "\n"
    )


def ask_yes_no(prompt: str, default_yes: bool = True) -> bool:
    d = "y" if default_yes else "n"
    ans = input(f"{prompt} (y/n) [default {d}]: ").strip().lower()
    if not ans:
        return default_yes
    return ans.startswith("y")


def show_full_text(text: str):
    """
    For very long transcripts, printing can appear 'cut' due to terminal scrollback.
    Use 'less' if available so the user can view the FULL output.
    """
    less = shutil.which("less")
    if less:
        try:
            # -R keeps ANSI safe if any, -S disables line wrap (horizontal scroll)
            p = subprocess.Popen([less, "-RS"], stdin=subprocess.PIPE, text=True)
            p.communicate(text)
            return
        except Exception:
            pass

    # Fallback: print. Note: terminal scrollback may still limit what you can scroll to.
    print(text)


# -----------------------------
# Transcript fetching (robust)
# -----------------------------
def normalize_entry(e) -> dict:
    """
    youtube-transcript-api versions may return dict entries or snippet objects.
    Normalize both to dict with text/start/duration.
    """
    if isinstance(e, dict):
        return {
            "text": e.get("text", "") or "",
            "start": float(e.get("start", 0.0) or 0.0),
            "duration": float(e.get("duration", 0.0) or 0.0),
        }
    # object style
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


def normalize_entries(entries) -> list[dict]:
    return [normalize_entry(e) for e in entries]


def list_and_choose_transcript(video_id: str):
    tl = YouTubeTranscriptApi.list_transcripts(video_id)
    choices = [t for t in tl]
    if not choices:
        raise RuntimeError("No transcripts available for this video.")

    print("\nAvailable transcript tracks:\n")
    for i, t in enumerate(choices, start=1):
        kind = "AUTO" if t.is_generated else "MANUAL"
        print(f"  [{i}] {t.language} ({t.language_code}) - {kind}")

    sel = input("\nChoose a track number [default 1]: ").strip()
    if not sel:
        return choices[0]

    try:
        idx = int(sel)
        if 1 <= idx <= len(choices):
            return choices[idx - 1]
    except ValueError:
        pass

    print("\nInvalid selection. Using default (1).")
    return choices[0]


def fetch_full_entries(video_id: str) -> list[dict]:
    """
    Primary: choose track from list_transcripts and fetch it.
    Fallback: get_transcript(video_id) if needed.
    """
    try:
        t = list_and_choose_transcript(video_id)
        entries = t.fetch()
        return normalize_entries(entries)
    except Exception as e1:
        # fallback
        try:
            entries = YouTubeTranscriptApi.get_transcript(video_id)
            return normalize_entries(entries)
        except Exception as e2:
            raise RuntimeError(f"Failed to fetch transcript.\n- Track fetch error: {e1}\n- Fallback error: {e2}")


# -----------------------------
# Formatting
# -----------------------------
def format_with_timestamps(entries: list[dict]) -> str:
    out = []
    for e in entries:
        text = (e["text"] or "").replace("\n", " ").strip()
        if not text:
            continue
        out.append(f"[{e['start']:.2f}s] {text}")
    return "\n".join(out).strip() + "\n"


def format_line_by_line(entries: list[dict]) -> str:
    out = []
    for e in entries:
        text = (e["text"] or "").replace("\n", " ").strip()
        if text:
            out.append(text)
    return "\n".join(out).strip() + "\n"


def format_paragraphs(entries: list[dict], gap_seconds: float = 1.25) -> str:
    """
    Merge caption lines into paragraphs using time gaps between caption START times.
    If start gap > gap_seconds -> new paragraph.
    """
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

    # Separate paragraphs with blank line
    return "\n\n".join(p for p in paras if p).strip() + "\n"


# -----------------------------
# Save helpers
# -----------------------------
def default_base(meta: dict, video_id: str) -> str:
    title = (meta.get("title") or "").strip()
    if title:
        return safe_filename(f"{title} - {video_id}")
    return safe_filename(video_id)


def save_as_prompt(base_default: str, suffix: str, content: str) -> str | None:
    out_dir = ensure_storage_dir()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_name = f"{base_default}_{stamp}{suffix}.txt"
    if not ask_yes_no("Save to Android shared storage?", default_yes=True):
        return None
    name = input(f"Filename [default: {default_name}]: ").strip()
    if not name:
        name = default_name
    if not name.lower().endswith(".txt"):
        name += ".txt"
    path = os.path.join(out_dir, safe_filename(name))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def save_all(base_default: str, header: str, ts: str, lines: str, paras: str) -> list[str]:
    out_dir = ensure_storage_dir()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    p1 = os.path.join(out_dir, f"{base_default}_{stamp}_timestamps.txt")
    p2 = os.path.join(out_dir, f"{base_default}_{stamp}_lines.txt")
    p3 = os.path.join(out_dir, f"{base_default}_{stamp}_paragraphs.txt")

    with open(p1, "w", encoding="utf-8") as f:
        f.write(header + ts)
    with open(p2, "w", encoding="utf-8") as f:
        f.write(header + lines)
    with open(p3, "w", encoding="utf-8") as f:
        f.write(header + paras)

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

    # helpful info
    print(f"\nFetched {len(entries)} transcript entries.\n")
    return video_id, meta, entries


def action_show_and_optional_save(mode: str):
    """
    mode: 'ts' | 'lines' | 'paras'
    """
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
    show_full_text(full)

    try:
        path = save_as_prompt(base, suffix, full)
        if path:
            print(f"\nSaved: {path}\n")
    except Exception as e:
        print(f"\nSave failed: {e}\n")
        print("If you haven't granted storage access, run: termux-setup-storage\n")


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

    if not ask_yes_no("Save ALL 3 formats to Android shared storage?", default_yes=True):
        return

    try:
        paths = save_all(base, header, ts, lines, paras)
        print("\nSaved:")
        for p in paths:
            print(f" - {p}")
        print()
    except Exception as e:
        print(f"\nSave failed: {e}\n")
        print("If you haven't granted storage access, run: termux-setup-storage\n")


# -----------------------------
# Program loop
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
