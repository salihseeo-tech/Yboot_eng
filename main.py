"""
🎬 English Long-Form Video Generator — v1.0
Groq AI + Pollinations AI + Edge TTS + MoviePy v2
3 Series: 🔥 Viral Trends | 📖 Untold Stories | 🤯 Mind-Blowing Facts
Target: 10-15 minutes per video | General audience
"""

import os
import sys
import time
import json
import random
import hashlib
import asyncio
import re
import requests

from datetime import datetime
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from groq import Groq
import edge_tts

# ══════════════════════════════════════════════
#  ⚙️  CONFIG
# ══════════════════════════════════════════════
GROQ_API_KEY      = os.environ.get("GROQ_API_KEY", "")
OUTPUT_DIR        = "output_en_long"
HISTORY_FILE      = "history_en_long.json"
VIDEO_W           = 1920
VIDEO_H           = 1080
FPS               = 24
SCENES_COUNT      = 28        # 28 scenes × ~25s = ~11-12 minutes
VOICE             = "en-US-GuyNeural"
SIMILARITY_THRESH = 0.50
MAX_IDEA_RETRIES  = 6

if not GROQ_API_KEY:
    print("❌ GROQ_API_KEY not found")
    sys.exit(1)

# ══════════════════════════════════════════════
#  📚 THREE SERIES
# ══════════════════════════════════════════════
SERIES = [
    {
        "id": "trends",
        "name": "Viral Trends Explained",
        "emoji": "🔥",
        "videos_per_cycle": 4,
        "idea_prompt": (
            "You are a top YouTube content creator specializing in viral trends. "
            "Suggest ONE compelling video title about a current viral trend, internet phenomenon, "
            "social movement, or cultural moment that people are talking about. "
            "The title must be under 12 words, attention-grabbing, and suitable for a general audience. "
            "Examples of the quality expected: "
            "'Why Everyone Is Obsessed With This New Lifestyle Trend', "
            "'The Viral Phenomenon That Took Over the Internet Overnight', "
            "'This Social Movement Is Changing How Millions Think'. "
            "Must be completely different from: {used}. "
            "Return the title only, nothing else."
        ),
        "story_prompt": (
            "You are a professional YouTube scriptwriter creating a 10-15 minute video about: {idea}\n\n"
            "Write {n} scenes. Each scene must be a full paragraph of 4-6 sentences "
            "that flows naturally when spoken aloud.\n\n"
            "STRICT RULES:\n"
            "- Scene 1: Hook — start with a shocking statement or question that grabs attention instantly\n"
            "- Scenes 2-4: Context — explain why this trend exists and where it came from\n"
            "- Scenes 5-10: Deep dive — explore different angles, real examples, and surprising details\n"
            "- Scenes 11-18: Impact — how it's changing society, psychology, or culture\n"
            "- Scenes 19-24: Controversy — present different perspectives fairly\n"
            "- Scenes 25-27: What's next — where this trend is heading\n"
            "- Scene 28: Conclusion — memorable closing thought that makes viewers think\n"
            "- Use conversational but intelligent English — like speaking to a smart friend\n"
            "- No filler phrases, no repetition, every sentence adds value\n\n"
            "Return ONLY this exact format:\n\n{template}"
        ),
        "image_style": (
            "cinematic viral social media trend visualization, "
            "dramatic modern aesthetic, bold colors, 4k ultra HD, professional photography"
        ),
        "bar_color":    (15, 0, 40),
        "text_color":   (255, 100, 200, 255),
        "accent_color": (200, 0, 255),
        "tags": ["viral", "trending", "explained", "culture", "society", "trend2025"],
        "category_id": "22",  # People & Blogs
    },
    {
        "id": "stories",
        "name": "Untold Stories",
        "emoji": "📖",
        "videos_per_cycle": 4,
        "idea_prompt": (
            "You are a professional documentary scriptwriter. "
            "Suggest ONE compelling video title about a true story, historical event, "
            "or real-life mystery that most people don't know about. "
            "The title must be under 12 words, dramatic, and curiosity-driven. "
            "Examples: "
            "'The True Story Behind the Greatest Heist Nobody Talks About', "
            "'The Man Who Fooled the Entire World for 30 Years', "
            "'The Real Events That Inspired the Most Famous Movie Ever Made'. "
            "Must be completely different from: {used}. "
            "Return the title only, nothing else."
        ),
        "story_prompt": (
            "You are a world-class documentary scriptwriter creating a 10-15 minute video about: {idea}\n\n"
            "Write {n} scenes. Each scene must be a full paragraph of 4-6 sentences "
            "that flows naturally when narrated.\n\n"
            "STRICT RULES:\n"
            "- Scene 1: Cold open — drop the viewer into the most dramatic moment of the story\n"
            "- Scenes 2-4: Setup — who are the key people, what was the world like at the time\n"
            "- Scenes 5-12: The story unfolds — build tension scene by scene chronologically\n"
            "- Scenes 13-18: The turning point — the moment everything changed\n"
            "- Scenes 19-23: Aftermath — what happened next, consequences, revelations\n"
            "- Scenes 24-26: Why it matters — what this story teaches us today\n"
            "- Scenes 27-28: Legacy — how this story lives on\n"
            "- Use a gripping narrative voice — like the best true crime podcasts\n"
            "- Use real names, dates, and places where known\n"
            "- No fabricated facts — if uncertain, use 'reportedly' or 'according to'\n\n"
            "Return ONLY this exact format:\n\n{template}"
        ),
        "image_style": (
            "cinematic documentary storytelling, dramatic lighting, "
            "film noir atmosphere, historical epic, 4k ultra HD, BBC documentary style"
        ),
        "bar_color":    (30, 10, 0),
        "text_color":   (255, 200, 80, 255),
        "accent_color": (220, 140, 0),
        "tags": ["truestory", "documentary", "untold", "history", "realstory", "mystery"],
        "category_id": "27",  # Education
    },
    {
        "id": "facts",
        "name": "Mind-Blowing Facts",
        "emoji": "🤯",
        "videos_per_cycle": 4,
        "idea_prompt": (
            "You are a science communicator like Vsauce or Kurzgesagt. "
            "Suggest ONE compelling video title about a mind-blowing scientific, "
            "psychological, or historical fact that most people don't know. "
            "The title must be under 12 words, curiosity-driven, and fascinating. "
            "Examples: "
            "'The Scientific Reason Your Brain Is Lying to You Right Now', "
            "'This Discovery Changed Everything We Knew About Human History', "
            "'Why Time Does Not Actually Exist the Way You Think It Does'. "
            "Must be completely different from: {used}. "
            "Return the title only, nothing else."
        ),
        "story_prompt": (
            "You are a science communicator like Vsauce creating a 10-15 minute video about: {idea}\n\n"
            "Write {n} scenes. Each scene must be a full paragraph of 4-6 sentences "
            "that flows naturally when spoken aloud.\n\n"
            "STRICT RULES:\n"
            "- Scene 1: Hook — open with a counterintuitive statement that challenges assumptions\n"
            "- Scenes 2-5: The basics — explain the concept clearly for a general audience\n"
            "- Scenes 6-12: Go deeper — layer in surprising complexity and real examples\n"
            "- Scenes 13-18: The implications — what does this mean for how we see the world\n"
            "- Scenes 19-22: Expert perspectives — what scientists/historians actually say\n"
            "- Scenes 23-26: Real-world applications — how this affects everyday life\n"
            "- Scenes 27-28: The big question — end with a thought-provoking open question\n"
            "- Style: intelligent, curious, enthusiastic — make complex ideas feel exciting\n"
            "- Use real studies, numbers, and examples — cite sources naturally in the script\n"
            "- No dumbing down — trust the audience to follow complex ideas\n\n"
            "Return ONLY this exact format:\n\n{template}"
        ),
        "image_style": (
            "Vsauce Kurzgesagt style scientific visualization, "
            "stunning infographic cinematic, deep space dramatic, 4k ultra HD"
        ),
        "bar_color":    (0, 20, 50),
        "text_color":   (100, 210, 255, 255),
        "accent_color": (0, 180, 255),
        "tags": ["mindblowing", "science", "facts", "psychology", "didyouknow", "vsauce"],
        "category_id": "27",
    },
]

# ══════════════════════════════════════════════
#  🔍 DUPLICATE CHECK — 3 Layers
# ══════════════════════════════════════════════
def normalize(text):
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()

def jaccard(a, b):
    wa, wb = set(normalize(a).split()), set(normalize(b).split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)

def is_duplicate(new_idea, used):
    nn  = normalize(new_idea)
    nkw = set(nn.split()[:4])
    for old in used:
        on = normalize(old)
        if nn == on:
            return True, old, 1.0
        s = jaccard(new_idea, old)
        if s >= SIMILARITY_THRESH:
            return True, old, s
        okw = set(on.split()[:4])
        ks  = len(nkw & okw) / max(len(nkw | okw), 1)
        if ks >= 0.65:
            return True, old, ks
    return False, None, 0.0

# ══════════════════════════════════════════════
#  📋 HISTORY
# ══════════════════════════════════════════════
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                data.setdefault("used_ideas", [])
                data.setdefault("videos", [])
                data.setdefault("series_tracker", {s["id"]: 0 for s in SERIES})
                data.setdefault("current_series_index", 0)
                data.setdefault("current_series_count", 0)
                return data
        except Exception as e:
            print(f"⚠️  history corrupt, starting fresh: {e}")
    return {
        "used_ideas": [],
        "videos": [],
        "series_tracker": {s["id"]: 0 for s in SERIES},
        "current_series_index": 0,
        "current_series_count": 0,
    }

def save_history(h):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(h, f, ensure_ascii=False, indent=2)

# ══════════════════════════════════════════════
#  🔄 SERIES ROTATION
# ══════════════════════════════════════════════
def get_current_series(history):
    idx    = history.get("current_series_index", 0) % len(SERIES)
    count  = history.get("current_series_count", 0)
    series = SERIES[idx]
    if count >= series["videos_per_cycle"]:
        idx    = (idx + 1) % len(SERIES)
        count  = 0
        series = SERIES[idx]
        print(f"🔄 New series: {series['emoji']} {series['name']}")
    history["current_series_index"] = idx
    history["current_series_count"] = count + 1
    return series

# ══════════════════════════════════════════════
#  🤖 Groq — IDEA
# ══════════════════════════════════════════════
def generate_idea(client, history, series):
    used      = history.get("used_ideas", [])
    used_list = ", ".join(used[-50:]) if used else "none"

    for attempt in range(1, MAX_IDEA_RETRIES + 1):
        try:
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": series["idea_prompt"].format(used=used_list)}],
                temperature=min(0.85 + attempt * 0.05, 1.3),
                max_tokens=100,
            )
            idea = resp.choices[0].message.content.strip().strip("\"'").strip("-").strip()
            if not idea:
                continue

            dup, matched, score = is_duplicate(idea, used)
            if dup:
                print(f"  ⚠️  Attempt {attempt}: Similar ({score:.0%}) to '{matched}'")
                used_list += f", {idea}"
                continue

            print(f"  ✅ Unique idea (attempt {attempt}): {idea}")
            history["used_ideas"].append(idea)
            return idea

        except Exception as e:
            print(f"  ⚠️  Groq error attempt {attempt}: {e}")
            time.sleep(4)

    fallback = f"Amazing Facts You Never Knew {datetime.now().strftime('%H%M%S')}"
    history["used_ideas"].append(fallback)
    return fallback

# ══════════════════════════════════════════════
#  🤖 Groq — SCRIPT (split into 2 calls for long scripts)
# ══════════════════════════════════════════════
def build_template(start, end):
    t = ""
    for i in range(start, end + 1):
        t += f"Scene {i}: [Full paragraph narration — 4 to 6 sentences]\nImage {i}: [Cinematic image description]\n\n"
    return t

def generate_story(idea, client, series):
    print("  ✍️  Writing script (Part 1)...")
    scenes_all = []

    # Split into 2 Groq calls to avoid token limits
    # Part 1: scenes 1-14
    prompt_1 = (
        f"{series['story_prompt'].split('Return ONLY')[0]}"
        f"Write scenes 1 to 14 ONLY.\n\n"
        f"Return ONLY this exact format:\n\n"
        f"{build_template(1, 14)}"
    ).format(idea=idea, n=SCENES_COUNT, template="")

    # Part 2: scenes 15-28
    prompt_2 = (
        f"Continue the video script about: {idea}\n"
        f"Write scenes 15 to 28. Keep the same tone and style as part 1.\n"
        f"Each scene: a full paragraph of 4-6 sentences.\n\n"
        f"Return ONLY this exact format:\n\n"
        f"{build_template(15, 28)}"
    )

    for part_num, prompt in enumerate([prompt_1, prompt_2], 1):
        print(f"  ✍️  Script Part {part_num}/2...")
        for attempt in range(3):
            try:
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.72,
                    max_tokens=4000,
                )
                content = resp.choices[0].message.content
                if content and content.strip():
                    scenes_all.append(content)
                    print(f"  ✅ Part {part_num} ready")
                    break
            except Exception as e:
                print(f"  ⚠️  Groq error part {part_num} attempt {attempt+1}: {e}")
                time.sleep(4)

    return "\n\n".join(scenes_all)

def parse_story(raw, idea, series):
    scenes, current = [], {}
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r"^Scene\s*\d+\s*:", line, re.IGNORECASE):
            if current:
                scenes.append(current)
            current = {"text": line.split(":", 1)[1].strip()}
        elif re.match(r"^Image\s*\d+\s*:", line, re.IGNORECASE):
            current["image_prompt"] = line.split(":", 1)[1].strip()
    if current:
        scenes.append(current)

    scenes = [s for s in scenes if s.get("text") and s.get("image_prompt")]

    # Fallback scenes if needed
    fallbacks = [
        ("This is one of the most remarkable things you'll ever learn about our world.", f"{idea}, dramatic cinematic visualization 4k"),
        ("The evidence behind this is more compelling than most people realize.", f"{idea}, scientific dramatic documentary style"),
        ("Experts have studied this for decades, and the findings are extraordinary.", f"{idea}, research laboratory cinematic"),
        ("What happened next changed everything we thought we knew.", f"{idea}, dramatic turning point cinematic"),
        ("The implications of this extend far beyond what most people imagine.", f"{idea}, wide angle epic visualization"),
        ("Real accounts from the time paint a vivid picture of just how significant this was.", f"{idea}, historical atmospheric cinematic"),
        ("When you look at the data, the patterns become impossible to ignore.", f"{idea}, data visualization dramatic"),
        ("This is the part of the story that most sources leave out entirely.", f"{idea}, hidden reveal dramatic cinematic"),
        ("The people involved had no idea they were making history.", f"{idea}, unaware historical moment cinematic"),
        ("And the ripple effects of this are still being felt today.", f"{idea}, ripple effect wide cinematic"),
        ("Scientists are only now beginning to understand the full scope of this.", f"{idea}, modern science discovery 4k"),
        ("The truth, as it turns out, is far stranger than the popular narrative.", f"{idea}, truth reveal dramatic atmospheric"),
        ("This single moment reshaped how millions of people think and behave.", f"{idea}, mass impact visualization"),
        ("The question this raises is one humanity may never fully answer.", f"{idea}, philosophical question dramatic"),
    ]

    while len(scenes) < SCENES_COUNT:
        i = len(scenes)
        t, p = fallbacks[i % len(fallbacks)]
        scenes.append({"text": t, "image_prompt": p})
        print(f"  ⚠️  Scene {i+1} from fallback")

    return scenes[:SCENES_COUNT]

# ══════════════════════════════════════════════
#  🖼️  Pollinations
# ══════════════════════════════════════════════
def generate_image(prompt, index, seed, series):
    print(f"  🖼️  Image {index}/{SCENES_COUNT}...")
    enhanced = f"{prompt}, {series['image_style']}"
    url = (
        "https://image.pollinations.ai/prompt/"
        + requests.utils.quote(enhanced)
        + f"?width={VIDEO_W}&height={VIDEO_H}&nologo=true&seed={seed + index * 11}"
    )
    for attempt in range(4):
        try:
            r = requests.get(url, timeout=150)
            r.raise_for_status()
            img  = Image.open(BytesIO(r.content)).convert("RGB")
            path = os.path.join(OUTPUT_DIR, f"tmp_scene_{index}.jpg")
            img.save(path, quality=92)
            return path
        except Exception as e:
            print(f"    ⚠️  Attempt {attempt+1}: {e}")
            time.sleep(6)

    # Gradient fallback
    bc   = series["bar_color"]
    img  = Image.new("RGB", (VIDEO_W, VIDEO_H), bc)
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_H):
        ratio = y / VIDEO_H
        r = min(255, int(bc[0] + ratio * 40))
        g = min(255, int(bc[1] + ratio * 20))
        b = min(255, int(bc[2] + ratio * 60))
        draw.rectangle([(0, y), (VIDEO_W, y + 1)], fill=(r, g, b))
    path = os.path.join(OUTPUT_DIR, f"tmp_scene_{index}.jpg")
    img.save(path)
    return path

# ══════════════════════════════════════════════
#  🖊️  Pillow — Professional subtitle
# ══════════════════════════════════════════════
def load_font(size):
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
        "/Library/Fonts/Arial.ttf",
    ]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size=size)
            except Exception:
                pass
    return ImageFont.load_default()

def wrap_text(text, max_chars=70):
    words, lines, line = text.split(), [], ""
    for w in words:
        if len(line) + len(w) + 1 <= max_chars:
            line = f"{line} {w}".strip()
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines[:4]   # up to 4 lines for long sentences

def add_subtitle(image_path, text, index, series):
    img     = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)
    bc, ac  = series["bar_color"], series["accent_color"]
    bar_h   = 220   # taller bar for longer text

    # Gradient bar
    for y in range(bar_h):
        a = int(230 * (1 - y / bar_h * 0.15))
        draw.rectangle(
            [(0, img.height - bar_h + y), (img.width, img.height - bar_h + y + 1)],
            fill=(bc[0], bc[1], bc[2], a)
        )

    # Accent line
    draw.rectangle(
        [(0, img.height - bar_h), (img.width, img.height - bar_h + 5)],
        fill=(ac[0], ac[1], ac[2], 230)
    )

    # Series badge
    bf = load_font(22)
    btext = f"{series['emoji']}  {series['name']}"
    bb    = draw.textbbox((0, 0), btext, font=bf)
    bw    = bb[2] - bb[0]
    draw.rectangle([(16, 16), (bw + 36, 52)], fill=(0, 0, 0, 190))
    draw.text((26, 20), btext, font=bf, fill=(255, 255, 255, 230))

    # Scene counter
    nf   = load_font(20)
    ntxt = f"{index} / {SCENES_COUNT}"
    nb   = draw.textbbox((0, 0), ntxt, font=nf)
    nw   = nb[2] - nb[0]
    draw.rectangle([(img.width - nw - 30, 16), (img.width - 12, 50)], fill=(0, 0, 0, 160))
    draw.text((img.width - nw - 20, 20), ntxt, font=nf, fill=(200, 200, 200, 210))

    # Main text
    font  = load_font(34)
    tc    = series["text_color"]
    lines = wrap_text(text)
    y     = img.height - bar_h + 22

    for line in lines:
        lb = draw.textbbox((0, 0), line, font=font)
        lw = lb[2] - lb[0]
        x  = (img.width - lw) // 2
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 210))
        draw.text((x, y),         line, font=font, fill=tc)
        y += 50

    out = os.path.join(OUTPUT_DIR, f"tmp_sub_{index}.jpg")
    Image.alpha_composite(img, overlay).convert("RGB").save(out, quality=92)
    return out

# ══════════════════════════════════════════════
#  🔊 Edge TTS
# ══════════════════════════════════════════════
def generate_audio(text, index):
    path = os.path.join(OUTPUT_DIR, f"tmp_audio_{index}.mp3")

    async def _speak():
        communicate = edge_tts.Communicate(
            text,
            VOICE,
            rate="-3%",    # slightly slower = clearer narration
            volume="+8%",
        )
        await communicate.save(path)

    asyncio.run(_speak())

    if not os.path.exists(path) or os.path.getsize(path) < 100:
        raise RuntimeError(f"Audio generation failed for scene {index}")

    return path

# ══════════════════════════════════════════════
#  🎬 MoviePy v2
# ══════════════════════════════════════════════
def create_video(scenes_data, output_name):
    print("\n🎬 Assembling video...")
    try:
        from moviepy import ImageClip, AudioFileClip, CompositeVideoClip
        from moviepy.video.fx import FadeIn, FadeOut
    except ImportError as e:
        print(f"❌ moviepy: {e}")
        sys.exit(1)

    FADE, clips, start = 0.8, [], 0.0

    for i, scene in enumerate(scenes_data):
        ap = scene.get("audio_path", "")
        sp = scene.get("subtitle_path", "")
        if not os.path.exists(ap) or not os.path.exists(sp):
            print(f"  ⚠️  Scene {i+1}: missing files — skipping")
            continue
        try:
            audio = AudioFileClip(ap)
            if audio.duration < 0.5:
                audio.close()
                continue
            dur  = audio.duration + 0.5
            clip = (
                ImageClip(sp).with_duration(dur)
                .with_audio(audio)
                .with_start(start)
                .with_effects([FadeIn(FADE), FadeOut(FADE)])
            )
            clips.append(clip)
            start += dur - FADE
        except Exception as e:
            print(f"  ⚠️  Scene {i+1} error: {e}")

    if not clips:
        print("❌ No valid clips")
        sys.exit(1)

    total    = start + clips[-1].duration
    mins     = int(total // 60)
    secs     = int(total % 60)
    print(f"  📏 Total duration: {mins}m {secs}s")

    final    = CompositeVideoClip(clips, size=(VIDEO_W, VIDEO_H)).with_duration(total)
    out_path = os.path.join(OUTPUT_DIR, output_name)
    final.write_videofile(
        out_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        logger=None,
        preset="fast",
    )
    print(f"  ✅ {out_path}")
    return out_path

# ══════════════════════════════════════════════
#  📺 YouTube
# ══════════════════════════════════════════════
def upload_to_youtube(video_path, metadata):
    creds_json = os.environ.get("YOUTUBE_CREDENTIALS_JSON", "")
    if not creds_json:
        print("⚠️  YOUTUBE_CREDENTIALS_JSON not set — skipping upload")
        return None
    try:
        import google.oauth2.credentials
        import googleapiclient.discovery
        import googleapiclient.http

        d     = json.loads(creds_json)
        creds = google.oauth2.credentials.Credentials(
            token         = d.get("token"),
            refresh_token = d.get("refresh_token"),
            token_uri     = "https://oauth2.googleapis.com/token",
            client_id     = d.get("client_id"),
            client_secret = d.get("client_secret"),
        )
        yt   = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
        body = {
            "snippet": {
                "title"      : metadata["title"],
                "description": metadata["description"],
                "tags"       : metadata["tags"],
                "categoryId" : metadata["category_id"],
            },
            "status": {"privacyStatus": "public"},
        }
        media    = googleapiclient.http.MediaFileUpload(
            video_path, mimetype="video/mp4", resumable=True, chunksize=2 * 1024 * 1024
        )
        req, res = yt.videos().insert(part="snippet,status", body=body, media_body=media), None
        print("📤 Uploading...")
        while res is None:
            status, res = req.next_chunk()
            if status:
                print(f"  ⬆️  {int(status.progress() * 100)}%")
        vid = res.get("id")
        print(f"  ✅ https://youtube.com/watch?v={vid}")
        return vid
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        return None

# ══════════════════════════════════════════════
#  🗑️  Cleanup
# ══════════════════════════════════════════════
def cleanup_temp():
    for f in os.listdir(OUTPUT_DIR):
        if f.startswith("tmp_"):
            try:
                os.remove(os.path.join(OUTPUT_DIR, f))
            except Exception:
                pass

# ══════════════════════════════════════════════
#  🚀 MAIN RUN
# ══════════════════════════════════════════════
def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("=" * 55)
    print("🎬 English Long-Form Video Generator v1.0")
    print(f"🎙️  Voice: {VOICE} | 🎞️  Scenes: {SCENES_COUNT}")
    print(f"📐 Resolution: {VIDEO_W}x{VIDEO_H}")
    print("=" * 55)

    client  = Groq(api_key=GROQ_API_KEY)
    history = load_history()
    series  = get_current_series(history)

    print(f"\n📺 Series  : {series['emoji']} {series['name']}")
    print(f"🔢 Video   : {history['current_series_count']}/{series['videos_per_cycle']}")
    print(f"📦 Saved ideas: {len(history.get('used_ideas', []))}\n")

    seed      = random.randint(10000, 99999)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("🧠 Generating unique idea...")
    idea      = generate_idea(client, history, series)
    slug      = hashlib.md5(idea.encode()).hexdigest()[:6]
    out_name  = f"{series['id']}_{timestamp}_{slug}.mp4"

    print(f"\n💡 {idea}")
    print(f"🔑 seed={seed} | 📁 {out_name}\n")

    raw    = generate_story(idea, client, series)
    scenes = parse_story(raw, idea, series)
    print(f"\n📋 {len(scenes)} scenes ready\n")

    for i, scene in enumerate(scenes, 1):
        print(f"⚙️  Scene {i}/{len(scenes)}")
        try:
            img_path               = generate_image(scene["image_prompt"], i, seed, series)
            scene["subtitle_path"] = add_subtitle(img_path, scene["text"], i, series)
            scene["audio_path"]    = generate_audio(scene["text"], i)
            print(f"  ✅ Done")
        except Exception as e:
            print(f"  ❌ Scene {i} failed: {e}")
            scene["subtitle_path"] = ""
            scene["audio_path"]    = ""

    video_path = create_video(scenes, out_name)
    cleanup_temp()

    metadata = {
        "title"      : f"{series['emoji']} {idea}",
        "description": (
            f"{idea}\n\n"
            f"{series['name']} — Deep dive into one of the most fascinating topics.\n\n"
            f"Subscribe for more! 🔔\n\n"
            f"#{' #'.join(series['tags'])}"
        ),
        "tags"       : series["tags"],
        "category_id": series["category_id"],
    }
    youtube_id = upload_to_youtube(video_path, metadata)

    history["series_tracker"][series["id"]] = \
        history["series_tracker"].get(series["id"], 0) + 1
    history["videos"].append({
        "file"      : out_name,
        "idea"      : idea,
        "series"    : series["id"],
        "created_at": timestamp,
        "seed"      : seed,
        "youtube"   : youtube_id,
    })
    save_history(history)

    print("\n" + "=" * 55)
    print("🎉 Complete!")
    print(f"📁 {video_path}")
    if youtube_id:
        print(f"📺 https://youtube.com/watch?v={youtube_id}")
    print(f"\n📊 Series stats:")
    for s in SERIES:
        print(f"   {s['emoji']} {s['name']}: {history['series_tracker'].get(s['id'], 0)} videos")
    print(f"\n📦 Total: {len(history['videos'])} videos")
    print(f"🧠 Saved ideas: {len(history['used_ideas'])}")
    print("=" * 55)
    return video_path


if __name__ == "__main__":
    run()
