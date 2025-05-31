# setup.py
from cx_Freeze import setup, Executable

build_options = {
    "packages": ["os", "sys", "cv2", "pygame", "yt_dlp", "threading", "subprocess", "shutil", "time"],
    "include_files": [],
    "excludes": [],
}

setup(
    name="YouTubeCLI",
    version="1.0",
    description="Play YouTube videos as ASCII art with audio in terminal.",
    options={"build_exe": build_options},
    executables=[Executable("video.py", base=None)]
)

