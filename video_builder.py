import subprocess
from pathlib import Path

def create_video_from_image(image_path: Path, audio_path: Path, output_path: Path, duration: int = 10) -> None:
    print(f"Generating {duration}s video from image and audio...")
    
    # We use a subtle zoom effect for the reel to give it life
    # zoompan filter: zooms in slowly to 1.05x over 300 frames (10 seconds at 30fps)
    command = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-i", str(audio_path),
        "-vf", "scale=1080x1350,zoompan=z='min(zoom+0.0005,1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=300",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Video saved to {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to generate video: {e.stderr.decode('utf-8', errors='ignore')}")
        raise
