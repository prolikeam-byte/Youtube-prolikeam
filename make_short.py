from pathlib import Path
import re
import sys
import textwrap

import numpy as np
import pyttsx3
from PIL import Image, ImageDraw, ImageFont, ImageOps
from moviepy import AudioFileClip, CompositeVideoClip, ImageClip, concatenate_videoclips

ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT / "input"
ASSETS_DIR = ROOT / "assets"
OUTPUT_DIR = ROOT / "output"
NARRATION_FILE = INPUT_DIR / "narration.txt"
VOICE_FILE = OUTPUT_DIR / "voiceover.wav"
OUTPUT_FILE = OUTPUT_DIR / "short.mp4"

WIDTH, HEIGHT = 1080, 1920
FPS = 30
MIN_SECONDS_PER_SCENE = 3.0


def ensure_folders():
    INPUT_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)


def make_voiceover(text):
    """Create offline speech using a voice installed in Windows."""
    engine = pyttsx3.init()
    engine.setProperty("rate", 165)
    engine.setProperty("volume", 1.0)

    # Use an installed English voice if one is available.
    try:
        voices = engine.getProperty("voices")
        for voice in voices:
            desc = (str(getattr(voice, "name", "")) + " " +
                    str(getattr(voice, "id", ""))).lower()
            if "english" in desc or "en-" in desc or "en_" in desc:
                engine.setProperty("voice", voice.id)
                break
    except Exception:
        pass

    engine.save_to_file(text, str(VOICE_FILE))
    engine.runAndWait()
    engine.stop()

    if not VOICE_FILE.exists() or VOICE_FILE.stat().st_size < 1000:
        raise RuntimeError(
            "Windows text-to-speech did not create voiceover.wav. "
            "Check that Windows has a speech voice installed, then try again."
        )


def find_images():
    allowed = {".png", ".jpg", ".jpeg", ".webp"}
    images = sorted(
        p for p in ASSETS_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in allowed
        and p.name.lower().startswith("scene_")
    )
    return images


def prepare_image(path, index):
    """Crop an image to fill a vertical 1080x1920 frame."""
    with Image.open(path) as source:
        image = ImageOps.fit(
            source.convert("RGB"),
            (WIDTH, HEIGHT),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
    out_path = OUTPUT_DIR / f"prepared_{index:02d}.jpg"
    image.save(out_path, quality=92)
    return out_path


def split_caption_chunks(text, words_per_caption=6):
    words = text.split()
    return [
        " ".join(words[i:i + words_per_caption])
        for i in range(0, len(words), words_per_caption)
    ]


def load_font(size):
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\Arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            try:
                return ImageFont.truetype(candidate, size)
            except Exception:
                pass
    return ImageFont.load_default()


def make_caption_image(caption):
    """Create a transparent overlay with readable subtitles."""
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = load_font(58)

    # Wrap caption to a maximum of two lines.
    lines = textwrap.wrap(caption, width=25)[:2]
    line_heights = []
    line_widths = []
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font, stroke_width=2)
        line_widths.append(box[2] - box[0])
        line_heights.append(box[3] - box[1])

    text_height = sum(line_heights) + 18 * max(0, len(lines) - 1)
    box_width = min(WIDTH - 100, max(line_widths, default=300) + 70)
    box_height = text_height + 44
    left = (WIDTH - box_width) // 2
    top = HEIGHT - 300

    draw.rounded_rectangle(
        (left, top, left + box_width, top + box_height),
        radius=28,
        fill=(0, 0, 0, 165),
    )

    y = top + 22
    for line, line_height in zip(lines, line_heights):
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=2)
        line_width = bbox[2] - bbox[0]
        x = (WIDTH - line_width) // 2
        draw.text(
            (x, y), line, font=font, fill=(255, 255, 255, 255),
            stroke_width=2, stroke_fill=(0, 0, 0, 220)
        )
        y += line_height + 18

    return np.array(overlay)


def main():
    ensure_folders()

    if not NARRATION_FILE.exists():
        raise FileNotFoundError(
            f"Missing {NARRATION_FILE}. Add your narration to input/narration.txt."
        )

    narration = NARRATION_FILE.read_text(encoding="utf-8").strip()
    if not narration:
        raise ValueError("input/narration.txt is empty. Paste your narration into it.")

    images = find_images()
    if not images:
        raise FileNotFoundError(
            "No scene images found. Add AI-generated images to assets/ and name "
            "them scene_01.png, scene_02.png, etc."
        )

    print("1/4 Creating offline voiceover...")
    make_voiceover(narration)

    print("2/4 Preparing vertical images...")
    prepared = [prepare_image(path, i + 1) for i, path in enumerate(images)]

    print("3/4 Building video and captions...")
    audio = AudioFileClip(str(VOICE_FILE))
    total_duration = max(audio.duration, len(prepared) * MIN_SECONDS_PER_SCENE)
    scene_duration = total_duration / len(prepared)

    scene_clips = [
        ImageClip(str(path)).with_duration(scene_duration)
        for path in prepared
    ]
    base_video = concatenate_videoclips(scene_clips, method="compose")

    caption_clips = []
    chunks = split_caption_chunks(narration)
    # Approximate caption timing by word count; review timing after export.
    word_counts = [max(1, len(chunk.split())) for chunk in chunks]
    total_words = sum(word_counts)
    cursor = 0.0
    for chunk, count in zip(chunks, word_counts):
        duration = audio.duration * count / total_words
        caption_array = make_caption_image(chunk)
        caption_clip = (
            ImageClip(caption_array, transparent=True)
            .with_start(cursor)
            .with_duration(max(0.1, duration))
            .with_position(("center", "center"))
        )
        caption_clips.append(caption_clip)
        cursor += duration

    final_video = CompositeVideoClip(
        [base_video, *caption_clips], size=(WIDTH, HEIGHT)
    ).with_audio(audio)

    print("4/4 Rendering output/short.mp4 (this can take a few minutes)...")
    final_video.write_videofile(
        str(OUTPUT_FILE),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=2,
        logger="bar",
    )

    final_video.close()
    base_video.close()
    audio.close()
    for clip in scene_clips + caption_clips:
        clip.close()

    print(f"\nDone! Your video is here:\n{OUTPUT_FILE}")
    print("Check the captions and voiceover before uploading.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)
