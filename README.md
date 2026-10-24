# YouTube AI Shorts Agent (Free Starter)

This beginner-friendly project turns a narration file and scene images into a vertical MP4 with offline Windows text-to-speech and approximate captions.

## What it does
- Reads `input/narration.txt`
- Creates a voiceover using a speech voice installed in Windows
- Uses images you put in `assets/` (AI-generate them with a free service)
- Crops images to vertical 1080x1920
- Adds captions based on the narration
- Renders `output/short.mp4`

## What it does NOT do
- It does not call Claude or require a Claude API key.
- It does not automatically generate AI images. Use Claude Free to write image prompts and an image generator's free tier to create images.
- Captions are timed approximately, so check them before publishing.
- It does not upload to YouTube.

## Windows setup

1. Install Python 3.11 or 3.12 from https://www.python.org/downloads/windows/
   - During setup, tick **Add python.exe to PATH**.
2. Download this repository using GitHub's **Code → Download ZIP**, then extract it.
3. Open the extracted `youtube-ai-agent` folder in File Explorer.
4. Click the address bar, type `cmd`, and press Enter.
5. Run these commands:

```bat
py -m venv .venv
.venv\Scripts\activate
py -m pip install --upgrade pip
pip install -r requirements.txt
```

6. Replace the sample text in `input/narration.txt` with your narration.
7. Put your AI-generated scene images into `assets/`, named in order:
   - `scene_01.png`
   - `scene_02.png`
   - `scene_03.png`
   - and so on.
   JPG and WEBP are also accepted.
8. Run:

```bat
python make_short.py
```

9. Your finished file will be `output\short.mp4`.

## Make a scene pack with Claude Free

Paste this prompt into https://claude.ai/:

> Create a 30-second original YouTube Short about: [YOUR TOPIC].
> Write narration of about 65–75 words. Then give me six detailed vertical 9:16 image prompts in scene order. Keep the character, clothing, lighting and art style consistent. Do not include written words inside the generated images. Also suggest a title and description. I will generate the images separately and assemble them locally.

Generate six images with a free image tool, save them using the filenames above, and use Claude's narration in `input/narration.txt`.

## Export and upload

The output is 1080x1920, 30 FPS, MP4 with H.264 video and AAC audio. Watch the entire file, check pronunciation and caption timing, and only upload content you have rights to use. YouTube upload is a separate manual step.

## Troubleshooting

- **`py` is not recognized:** reinstall Python and tick “Add Python to PATH”, then reopen Command Prompt.
- **No voiceover generated:** make sure Windows has a speech voice installed; try Windows Settings → Time & language → Speech.
- **No images found:** check the names begin with `scene_` and files are inside `assets`.
- **Install error:** try `py -m pip install -r requirements.txt` after activating `.venv`.
- **Rendering is slow:** close other apps and start with three or four images.
