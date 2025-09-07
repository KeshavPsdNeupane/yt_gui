# yt-dlp Multi Downloader GUI

A simple Python GUI for downloading videos and audio using yt-dlp and ffmpeg, supporting cookies from multiple browsers. Note: For restricted websites such as YouTube, you must manually add a cookies.txt file exported from your browser, because Chrome and some other browsers do not generate it automatically.

---

## Features

- Download single videos or playlists.
- Automatically separates downloads into **Audio** and **Video** folders.
- Supports **cookies.txt** for authenticated downloads.
- Config stored in `C:/yt_gui/data/`.
- Default download folder: `C:/yt_gui/download/`.
- Progress bar with status messages.
- Cross-browser cookie detection if `cookies.txt` is missing.
- No console window when running (PyInstaller built with `--noconsole`).

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/yt_gui.git
cd yt_gui
```

2. Make sure yt-dlp.exe and ffmpeg.exe are in the project root.
3. Install dependencies from requirement, (tkinter is included in standard Python on Windows, usually no extra install required)

# Usage

## Run the GUI:

```bash
python yt_gui.py
```

1. Enter the video or playlist URL.
2. Select download folder (optional; default is C:/yt_gui/download/).
3. Choose Video/Audio, format, and quality.
4. Click Add to Queue and then Download.

# PyInstaller Build

## To create a standalone .exe:

```bash
pyinstaller --onefile --noconsole --add-binary "yt-dlp.exe;." --add-binary "ffmpeg.exe;." yt_gui.py
```
