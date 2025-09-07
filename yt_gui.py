import tkinter as tk
from tkinter import filedialog, ttk
import subprocess
import threading
import os
import sys
import json
from typing import Optional, TextIO, cast

# -------------------------------
# Paths
# -------------------------------
BASE_DIR = "C:/yt_gui"
DATA_DIR = os.path.join(BASE_DIR, "data")
DOWNLOAD_DIR = os.path.join(BASE_DIR, "download")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(DATA_DIR, "yt_gui_config.json")
COOKIE_FILE = os.path.join(DATA_DIR, "cookies.txt")

# -------------------------------
# Paths for binaries
# -------------------------------
def get_yt_dlp_path():
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
        return os.path.join(base_path, "yt-dlp.exe")
    return "yt-dlp.exe"

def get_ffmpeg_path():
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
        return os.path.join(base_path, "ffmpeg.exe")
    return "ffmpeg.exe"

YTDLP_PATH = get_yt_dlp_path()
FFMPEG_PATH = get_ffmpeg_path()

# -------------------------------
# Config load/save
# -------------------------------
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except:
        config = {}
else:
    config = {}

for mode in ["single", "playlist"]:
    if mode not in config:
        config[mode] = {"download_folder": DOWNLOAD_DIR, "downloads": []}

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

# -------------------------------
# Helper functions
# -------------------------------
def browse_folder(var: tk.StringVar):
    folder = filedialog.askdirectory()
    if folder:
        var.set(folder)
        save_config()

def build_command(url: str, folder: str, type_format: str, is_audio: bool, quality: str = "Highest"):
    output_template = os.path.join(folder, "%(title)s.%(ext)s")
    
    common_flags = [
        "--ffmpeg-location", FFMPEG_PATH,
        "--no-check-certificate",
        "--ignore-errors",
        "--geo-bypass"
    ]

    # Use cookies.txt if it exists
    if os.path.exists(COOKIE_FILE):
        common_flags += ["--cookies", COOKIE_FILE]
    else:
        # Fallback to multi-browser detection
        BROWSERS = ["chrome", "firefox", "edge", "opera", "brave"]
        for browser in BROWSERS:
            common_flags += ["--cookies-from-browser", browser]
            break

    if is_audio:
        command = [
            YTDLP_PATH,
            "-f", "bestaudio/best",
            "--extract-audio",
            "--audio-format", type_format,
            "-o", output_template
        ] + common_flags + [url]
    else:
        fmt = {
            "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "Highest": "bestvideo+bestaudio/best"
        }[quality]
        command = [
            YTDLP_PATH,
            "-f", fmt,
            "--merge-output-format", type_format,
            "-o", output_template
        ] + common_flags + [url]
    return command

# -------------------------------
# DownloadItem class
# -------------------------------
class DownloadItem:
    def __init__(self, parent_frame, url, folder_var):
        self.url = url
        self.folder_var = folder_var
        self.process: Optional[subprocess.Popen] = None
        self.command = None

        self.frame = tk.Frame(parent_frame, relief="groove", bd=1, padx=5, pady=5)
        self.frame.pack(fill="x", pady=2)

        tk.Label(self.frame, text=url, wraplength=500, anchor="w", justify="left").pack(anchor="w")

        # Type drawer (Audio/Video)
        self.type_var = tk.StringVar(value="Video")
        type_menu = tk.OptionMenu(self.frame, self.type_var, "Video", "Audio", command=self.update_format_options)
        type_menu.pack(side="left", padx=5)

        # Format drawer
        self.format_var = tk.StringVar(value="mp4")
        self.format_menu = tk.OptionMenu(self.frame, self.format_var, "mp4", "mkv", "webm")
        self.format_menu.pack(side="left", padx=5)

        # Quality drawer (for video)
        self.quality_var = tk.StringVar(value="Highest")
        self.quality_menu = tk.OptionMenu(self.frame, self.quality_var, "360p","480p","720p","1080p","Highest")
        self.quality_menu.pack(side="left", padx=5)

        # Download button
        tk.Button(self.frame, text="Download", command=self.start).pack(side="left", padx=5)

        # Progress
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.frame, variable=self.progress_var, maximum=100, length=400)
        self.progress_bar.pack(pady=5)
        self.progress_label = tk.Label(self.frame, text="Idle")
        self.progress_label.pack(anchor="w")

        self.update_format_options(self.type_var.get())

    def update_format_options(self, value):
        menu = self.format_menu["menu"]
        menu.delete(0, "end")
        if value == "Audio":
            audio_formats = ["mp3", "m4a", "wav", "aac"]
            self.format_var.set(audio_formats[0])
            self.quality_menu.config(state="disabled")
            for fmt in audio_formats:
                menu.add_command(label=fmt, command=lambda f=fmt: self.format_var.set(f))
        else:
            video_formats = ["mp4", "mkv", "webm"]
            self.format_var.set(video_formats[0])
            self.quality_menu.config(state="normal")
            for fmt in video_formats:
                menu.add_command(label=fmt, command=lambda f=fmt: self.format_var.set(f))

    def start(self):
        folder = self.folder_var.get() or DOWNLOAD_DIR
        # Create subfolder based on type
        subfolder = "Audio" if self.type_var.get() == "Audio" else "Video"
        folder = os.path.join(folder, subfolder)
        os.makedirs(folder, exist_ok=True)
        self.folder_var.set(folder)
        
        is_audio = self.type_var.get() == "Audio"
        self.command = build_command(
            self.url,
            folder,
            self.format_var.get(),
            is_audio,
            self.quality_var.get()
        )
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        if self.command is None:
            return
        self.progress_label.config(text="Starting...")
        self.progress_bar.pack(pady=5)
        self.process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW  # prevents console
        )
        assert self.process.stdout is not None
        stdout: TextIO = cast(TextIO, self.process.stdout)

        output_lines = []

        for line in stdout:
            line = line.strip()
            output_lines.append(line)
            if line.startswith("[download]") and "%" in line:
                try:
                    percent = float(line.split("%")[0].split()[-1])
                    self.progress_var.set(percent)
                    self.progress_label.config(text=line)
                except:
                    pass

        self.process.wait()
        if self.process.returncode == 0:
            self.progress_label.config(text="Completed")
            self.progress_bar.pack_forget()
        else:
            self.progress_label.config(text="Failed")
            error_text = "\n".join(output_lines)
            self.show_error_window(error_text)
        self.process = None

    def show_error_window(self, text):
        win = tk.Toplevel()
        win.title("Download Error")
        win.geometry("600x400")
        tk.Label(win, text="Download Failed! Full output below:").pack(anchor="w", padx=10, pady=5)
        txt = tk.Text(win, wrap="word")
        txt.pack(expand=True, fill="both", padx=10, pady=5)
        txt.insert("1.0", text)
        txt.configure(state="normal")
        tk.Button(win, text="Close", command=win.destroy).pack(pady=5)

# -------------------------------
# TabPage class
# -------------------------------
class TabPage:
    def __init__(self, notebook, mode):
        self.mode = mode
        self.frame = tk.Frame(notebook)
        notebook.add(self.frame, text="Single Video" if mode=="single" else "Playlist")

        self.url_var = tk.StringVar()
        tk.Label(self.frame, text="URL:").pack(anchor="w", padx=10, pady=2)
        tk.Entry(self.frame, textvariable=self.url_var, width=80).pack(padx=10)

        # Download folder
        tk.Label(self.frame, text="Download Folder:").pack(anchor="w", padx=10)
        self.folder_var = tk.StringVar(value=config[mode].get("download_folder", DOWNLOAD_DIR))
        f_frame = tk.Frame(self.frame)
        f_frame.pack(fill="x", padx=10)
        tk.Entry(f_frame, textvariable=self.folder_var, width=55).pack(side="left", fill="x", expand=True)
        tk.Button(f_frame, text="Browse", command=lambda: browse_folder(self.folder_var)).pack(side="left", padx=5)

        # Add to queue
        tk.Button(self.frame, text="Add to Queue", bg="blue", fg="white", command=self.add_download).pack(pady=5)

        self.queue_frame = tk.Frame(self.frame)
        self.queue_frame.pack(fill="both", expand=True)

        self.download_items = []

    def add_download(self):
        url = self.url_var.get().strip()
        if url:
            item = DownloadItem(self.queue_frame, url, self.folder_var)
            self.download_items.append(item)
            self.url_var.set("")
            # Save to config
            config[self.mode]["downloads"].append({"url":url})
            config[self.mode]["download_folder"] = self.folder_var.get()
            save_config()

# -------------------------------
# Main GUI
# -------------------------------
root = tk.Tk()
root.title("yt-dlp Multi Downloader")
root.geometry("900x700")

# Default folder label
tk.Label(root, text=f"Default download folder: {DOWNLOAD_DIR}", bg="lightgrey", anchor="w").pack(fill="x", padx=5, pady=2)

# Notebook for Single/Playlist tabs
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

tab_single = TabPage(notebook, "single")
tab_playlist = TabPage(notebook, "playlist")

root.mainloop()
