import sys
import cv2
import os
import time
import shutil
import threading
import subprocess
import pygame
import yt_dlp

# More granular ASCII chars for better detail
ASCII_CHARS = "@%#*+=-:. "

def download_youtube_video_yt_dlp(url, output_path="."):
    ydl_opts = {
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_path = ydl.prepare_filename(info_dict)
        if not video_path.endswith('.mp4'):
            video_path = os.path.splitext(video_path)[0] + '.mp4'
        return video_path

def extract_audio(video_path, audio_path):
    command = ['ffmpeg', '-y', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', audio_path]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def rgb_to_gray(r, g, b):
    return 0.299*r + 0.587*g + 0.114*b

def pixel_to_ascii(pixel):
    b, g, r = pixel  # OpenCV uses BGR
    gray = rgb_to_gray(r, g, b)
    try:index = int(gray / 255 * (len(ASCII_CHARS) - 1))
    except (
            KeyboardInterrupt, EOFError):
        print("\nVideo playback interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error converting pixel to ASCII: {e}")
        index = 0
    return ASCII_CHARS[index], r, g, b

def get_terminal_size():
    cols, lines = shutil.get_terminal_size(fallback=(80, 24))
    # Use full terminal height for maximum video size
    return cols, lines

def calculate_dimensions(video_width, video_height, term_width, term_height):
    # Character aspect ratio (width:height)
    char_aspect = 0.5
    
    # Calculate video aspect ratio
    video_aspect = video_width / video_height
    
    # Calculate terminal aspect ratio (accounting for character aspect)
    term_aspect = (term_width * char_aspect) / term_height
    
    if video_aspect > term_aspect:
        # Video is wider relative to height
        new_width = term_width
        new_height = int(term_width / (video_aspect * 2))  # Multiply by 2 to account for character aspect
    else:
        # Video is taller relative to width
        new_height = term_height
        new_width = int(term_height * video_aspect * 2)  # Multiply by 2 to account for character aspect
    
    # Ensure dimensions don't exceed terminal size
    new_width = min(new_width, term_width)
    new_height = min(new_height, term_height)
    
    return new_width, new_height

def frame_to_ascii_color(frame, term_width, term_height):
    height, width = frame.shape[:2]
    
    # Calculate optimal dimensions to fill the terminal
    new_width, new_height = calculate_dimensions(width, height, term_width, term_height)
    
    # Resize frame
    resized = cv2.resize(frame, (new_width, new_height))
    
    # Convert frame to ASCII art
    ascii_art = []
    for y in range(new_height):
        line = ""
        for x in range(new_width):
            char, r, g, b = pixel_to_ascii(resized[y][x])
            line += f"\x1b[38;2;{r};{g};{b}m{char}\x1b[0m"
        ascii_art.append(line)
    
    # Center the ASCII art vertically
    padding_top = (term_height - len(ascii_art)) // 2
    padding_lines = [""] * padding_top
    
    return "\n".join(padding_lines + ascii_art)

def play_audio(audio_path):
    pygame.mixer.init()
    pygame.mixer.music.load(audio_path)
    pygame.mixer.music.play()



def play_video_ascii_color(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_duration = 1 / fps if fps > 0 else 0.03

    start_time = time.time()
    frame_index = 0

    try:
        print("\033[?25l", end="", flush=True)  # Hide cursor

        while True:
            # 현재 시각과 다음 출력할 프레임 시간 비교
            current_time = time.time()
            expected_time = start_time + frame_index * frame_duration

            # 밀린 경우: 프레임 스킵
            if current_time > expected_time + frame_duration:
                # 건너뛸 프레임 개수 계산
                frames_to_skip = int((current_time - expected_time) / frame_duration)
                for _ in range(frames_to_skip):
                    cap.read()
                    frame_index += 1

            ret, frame = cap.read()
            if not ret:
                break

            term_width, term_height = get_terminal_size()
            ascii_frame = frame_to_ascii_color(frame, term_width, term_height)

            print("\033[H" + ascii_frame, end="", flush=True)
            frame_index += 1

            # 다음 프레임까지 남은 시간 기다림
            sleep_time = expected_time + frame_duration - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

    finally:
        print("\033[?25h", end="", flush=True)  # Show cursor
        cap.release()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python video.py [YouTube_Video_ID]")
        sys.exit(1)
    
    url = f"https://www.youtube.com/watch?v={sys.argv[1]}"
    print("Downloading video...")
    try:
        video_path = download_youtube_video_yt_dlp(url, output_path="~/youtube.cli/")
    except KeyboardInterrupt:
        print("\nDownload interrupted by user.")
        sys.exit(0)
    print(f"Downloaded video saved to: {video_path}")
    
    audio_path = "audio.wav"
    print("Extracting audio...")
    try:
        extract_audio(video_path, audio_path)
    except KeyboardInterrupt:
        print("\nAudio extraction interrupted by user.")
        sys.exit(0)
    print("Playing video and audio...")
    print("Press Ctrl+C to stop playback")
    
    # Clear screen and save cursor position
    try:print("\033[2J\033[H", end="", flush=True)
    except KeyboardInterrupt:
        print("\nPlayback interrupted by user.")
        sys.exit(0)
    try:
        audio_thread = threading.Thread(target=play_audio, args=(audio_path,), daemon=True)
        audio_thread.start()
        
        play_video_ascii_color(video_path)
    except KeyboardInterrupt:    
        print("\nPlayback interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error during playback: {e}")\

    finally:
        if 'audio_thread' in locals() and audio_thread.is_alive():
            audio_thread.join(timeout=1)(video_path)


