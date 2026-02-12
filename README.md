# Transcriptor (Windows)
```___________                                          __         __                 
\__    ___/___________    ____   ______ ____ _______|__|_____ _/  |_  ____ _______ 
  |    |  \_  __ \__  \  /    \ /  ___// ___\\_  __ \  |____ \\   __\/ __ \\_  __ \
  |    |   |  | \// __ \_   |  \\___ \\  \___ |  | \/  |  |_\ \|  | (  \_\ )|  | \/
  |____|   |__|  (____  /___|  /____  \\___  /|__|  |__|   ___/|__|  \____/ |__|   
                      \/     \/     \/     \/          |__|                        
```
**By the BGGG — Background Gremlin Group**

Transcriptor is a simple Windows command-line tool that pulls **full YouTube transcripts** (captions) and formats them in multiple readable styles, with reliable viewing and saving for **long transcripts**.

> ✅ No browser extensions  
> ✅ No YouTube API key needed  
> ✅ Works with long transcripts (pager support)  
> ✅ Saves clean `.txt` exports

---

## Features

- **Full transcript fetch** using YouTube captions (via `youtube-transcript-api`)
- **Transcript track picker** (choose language + MANUAL/AUTO captions)
- Export formats:
  - **Timestamps**: `[12.34s] line…`
  - **Line-by-line**: one caption entry per line
  - **Paragraph mode**: merges entries into paragraphs using a time-gap rule
- **Save ALL** formats in one go
- **Long transcript friendly**
  - Optional pager viewing using Windows `more` so output doesn't appear "cut off"
- Metadata header included:
  - *Developed by the BGGG*
  - YouTube **Title**, **Channel**, and **Video URL** (via oEmbed when available)

---

## Requirements

- Windows 10 / 11
- **Python 3.10+** recommended (3.8+ usually works)
- Internet connection (to fetch captions + metadata)

---

## Install

1) Install Python from python.org  
   - During install, check: **“Add Python to PATH”**

2) Install the dependency:

```powershell
py -m pip install --upgrade pip
py -m pip install youtube-transcript-api


---

Usage

Run in PowerShell from the folder containing the script:

py .\transcriptor.py

You’ll see a menu like:

Pull transcript WITH timestamps

Pull transcript WITHOUT timestamps (line-by-line)

Pull transcript WITHOUT timestamps (paragraphs)

Save ALL formats

Help / Exit



---

Output Files

By default, Transcriptor saves files in:

.\Transcripts\

Example filenames:

Video Title - VIDEOID_YYYYMMDD_HHMMSS_timestamps.txt

Video Title - VIDEOID_YYYYMMDD_HHMMSS_lines.txt

Video Title - VIDEOID_YYYYMMDD_HHMMSS_paragraphs.txt



---

Notes on “Full Transcript”

Transcriptor pulls what YouTube provides as caption tracks. Some videos have multiple tracks (MANUAL vs AUTO, different languages). If your transcript looks shorter than what you see on YouTube:

Try a different track in the picker

Prefer MANUAL captions when available

Some videos restrict transcript access in ways that can affect third-party tools



---

Troubleshooting

Output seems “cut off”

Windows terminals have scrollback limits. When prompted, choose:

> View using pager (recommended for long transcripts)? (y/n)



Selecting y uses more, letting you scroll the entire transcript safely.

No transcript available

Some videos have:

captions disabled

region/age/private restrictions

auto captions not generated



---

Disclaimer

Transcriptor uses publicly available caption data. we're not responsible for what you do with it or how you use it. We neither endorse the use nor misuse of our products. all code is presented as is 

---

Credits

Transcriptor
Developed by the BGGG — Background Gremlin Group
