"""
🎬 Arabic Story Video Generator — AUTO MODE v3
Groq AI + Pollinations AI + Edge TTS + MoviePy v2
يشتغل محلياً وعلى GitHub Actions
"""

import os, sys, time, json, random, hashlib, requests, asyncio, edge_tts
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from groq import Groq

# ══════════════════════════════════════════════
#  ⚙️  الإعدادات — تُقرأ من environment variables
# ══════════════════════════════════════════════
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
OUTPUT_DIR   = "output"
HISTORY_FILE = "history.json"
VIDEO_W      = 1024
VIDEO_H      = 576
FPS          = 24
SCENES_COUNT = 8
VOICE        = "ar-SA-HamedNeural"

if not GROQ_API_KEY:
    print("❌ GROQ_API_KEY غير موجود في environment variables")
    sys.exit(1)

# ══════════════════════════════════════════════
#  📋 السجل
# ══════════════════════════════════════════════
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"used_ideas": [], "videos": []}

def save_history(h):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(h, f, ensure_ascii=False, indent=2)

# ══════════════════════════════════════════════
#  🤖 Groq — فكرة تلقائية
# ══════════════════════════════════════════════
def generate_idea(client, history):
    used      = history.get("used_ideas", [])
    used_list = ", ".join(used[-20:]) if used else "لا يوجد"
    prompt    = (
        "اقترح فكرة واحدة فقط لقصة قصيرة عربية مبدعة ومشوقة. "
        "الفكرة تكون جملة قصيرة 10 كلمات أو أقل. "
        "يجب أن تكون مختلفة تماماً عن: " + used_list +
        ". أرجع الفكرة فقط بدون أي نص إضافي."
    )
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.95,
    )
    idea = resp.choices[0].message.content.strip().strip('"\'').strip("-").strip()
    history["used_ideas"].append(idea)
    return idea

# ══════════════════════════════════════════════
#  🤖 Groq — القصة (8 مشاهد)
# ══════════════════════════════════════════════
def generate_story(idea, client):
    print("   جاري كتابة القصة...")
    scenes_template = ""
    for i in range(1, SCENES_COUNT + 1):
        scenes_template += (
            f"مشهد {i}: [النص العربي — جملة أو جملتان]\n"
            f"صورة {i}: [وصف إنجليزي سينمائي، cinematic, high quality]\n\n"
        )
    prompt = (
        f"اكتب قصة قصيرة بالعربي الفصيح البسيط عن: {idea}\n"
        f"القصة تكون {SCENES_COUNT} مشاهد. كل مشهد جملة أو جملتان.\n"
        f"أرجع الرد بهذا الشكل بالضبط، بدون أي نص إضافي:\n\n"
        + scenes_template
    )
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85,
    )
    print("   ✅ القصة جاهزة")
    return resp.choices[0].message.content

def parse_story(raw, idea):
    scenes, current = [], {}
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("مشهد"):
            if current:
                scenes.append(current)
            current = {"text": line.split(":", 1)[1].strip()}
        elif line.startswith("صورة"):
            current["image_prompt"] = line.split(":", 1)[1].strip()
    if current:
        scenes.append(current)
    if not scenes:
        print("⚠️  فشل التحليل، fallback...")
        base = [
            ("كانت البداية من هنا...",        "cinematic opening scene, dramatic lighting"),
            ("واجه البطل أول التحديات.",       "hero faces first challenge, epic"),
            ("لم يكن الطريق سهلاً.",           "difficult journey, moody cinematic"),
            ("كانت اللحظة الفارقة.",           "turning point moment, intense dramatic"),
            ("وجد في نفسه قوة لم يعرفها.",    "inner strength discovery, glowing light"),
            ("قرر المضي قدماً رغم كل شيء.",   "determined hero moving forward, epic"),
            ("وأخيراً لاحت بوادر الأمل.",      "hope emerging, golden light breaking"),
            ("وعاش يحمل الذكرى إلى الأبد.",   "peaceful hopeful ending, golden hour"),
        ]
        scenes = [{"text": t, "image_prompt": f"{idea}, {p}"} for t, p in base]
    return scenes[:SCENES_COUNT]

# ══════════════════════════════════════════════
#  🖼️  Pollinations — الصور
# ══════════════════════════════════════════════
def generate_image(prompt, index, seed):
    print(f"   🖼️  صورة {index}/{SCENES_COUNT}...")
    enhanced = f"{prompt}, cinematic, 4k, high detail, dramatic lighting"
    url = (
        "https://image.pollinations.ai/prompt/"
        + requests.utils.quote(enhanced)
        + f"?width={VIDEO_W}&height={VIDEO_H}&nologo=true&seed={seed + index * 7}"
    )
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=90)
            resp.raise_for_status()
            img  = Image.open(BytesIO(resp.content)).convert("RGB")
            path = os.path.join(OUTPUT_DIR, f"tmp_scene_{index}.jpg")
            img.save(path, quality=95)
            return path
        except Exception as e:
            print(f"      ⚠️  محاولة {attempt+1}: {e}")
            time.sleep(4)
    colors = ["#1a1a2e","#16213e","#0f3460","#533483","#2d6a4f","#1b4332","#370617","#03045e"]
    img  = Image.new("RGB", (VIDEO_W, VIDEO_H), colors[index % len(colors)])
    path = os.path.join(OUTPUT_DIR, f"tmp_scene_{index}.jpg")
    img.save(path)
    return path

# ══════════════════════════════════════════════
#  🖊️  Pillow — نص عربي على الصورة
# ══════════════════════════════════════════════
def add_subtitle(image_path, text, index):
    img     = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    bar_h = 130
    for y in range(bar_h):
        alpha = int(200 * (1 - y / bar_h * 0.3))
        draw.rectangle(
            [(0, img.height - bar_h + y), (img.width, img.height - bar_h + y + 1)],
            fill=(0, 0, 0, alpha)
        )

    font = None
    for fp in [
        # Linux (GitHub Actions / Ubuntu)
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        # Windows
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        # macOS
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, size=32)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()

    if len(text) > 40:
        mid = len(text) // 2
        sp  = text.rfind(" ", 0, mid + 12)
        lines = [text[:sp if sp != -1 else mid].strip(),
                 text[sp  if sp != -1 else mid:].strip()]
    else:
        lines = [text]

    y = img.height - bar_h + 22
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        tw = bb[2] - bb[0]
        x  = (img.width - tw) // 2
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                draw.text((x + dx, y + dy), line, font=font, fill=(180, 140, 0, 60))
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 230))
        draw.text((x, y),         line, font=font, fill=(255, 248, 200, 255))
        y += 45

    merged = Image.alpha_composite(img, overlay).convert("RGB")
    out    = os.path.join(OUTPUT_DIR, f"tmp_sub_{index}.jpg")
    merged.save(out, quality=95)
    return out

# ══════════════════════════════════════════════
#  🔊 Edge TTS — ولد سعودي
# ══════════════════════════════════════════════
def generate_audio(text, index):
    path = os.path.join(OUTPUT_DIR, f"tmp_audio_{index}.mp3")
    async def _speak():
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(path)
    asyncio.run(_speak())
    return path

# ══════════════════════════════════════════════
#  🎬 MoviePy v2 — تجميع مع FadeIn/FadeOut
# ══════════════════════════════════════════════
def create_video(scenes_data, output_name):
    print("\n🎬 جاري تجميع الفيديو...")
    try:
        from moviepy import ImageClip, AudioFileClip, CompositeVideoClip
        from moviepy.video.fx import FadeIn, FadeOut
    except ImportError:
        print("❌ moviepy غير مثبتة: pip install moviepy")
        sys.exit(1)

    FADE  = 0.5
    clips = []
    start = 0.0

    for i, scene in enumerate(scenes_data):
        audio    = AudioFileClip(scene["audio_path"])
        duration = audio.duration + 0.8
        clip = (
            ImageClip(scene["subtitle_path"], duration=duration)
            .with_audio(audio)
            .with_start(start)
            .with_effects([FadeIn(FADE), FadeOut(FADE)])
        )
        clips.append(clip)
        start += duration - FADE

    total = start + clips[-1].duration if clips else 0
    final = CompositeVideoClip(clips, size=(VIDEO_W, VIDEO_H)).with_duration(total)
    out_path = os.path.join(OUTPUT_DIR, output_name)
    final.write_videofile(
        out_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        logger=None,
    )
    return out_path

# ══════════════════════════════════════════════
#  📺 YouTube — رفع الفيديو
# ══════════════════════════════════════════════
def upload_to_youtube(video_path, metadata):
    try:
        import google.oauth2.credentials
        import googleapiclient.discovery
        import googleapiclient.http

        creds_json = os.environ.get("YOUTUBE_CREDENTIALS_JSON", "")
        if not creds_json:
            print("⚠️  YOUTUBE_CREDENTIALS_JSON غير موجود، تخطي النشر")
            return None

        creds_data = json.loads(creds_json)
        creds = google.oauth2.credentials.Credentials(
            token         = creds_data.get("token"),
            refresh_token = creds_data.get("refresh_token"),
            token_uri     = "https://oauth2.googleapis.com/token",
            client_id     = creds_data.get("client_id"),
            client_secret = creds_data.get("client_secret"),
        )

        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title"      : metadata["title"],
                "description": metadata["description"],
                "tags"       : metadata["tags"],
                "categoryId" : "24",  # Entertainment
            },
            "status": {
                "privacyStatus": "public",
            },
        }

        media = googleapiclient.http.MediaFileUpload(
            video_path,
            mimetype    = "video/mp4",
            resumable   = True,
            chunksize   = 1024 * 1024,
        )

        request  = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = None
        print("📤 جاري رفع الفيديو على يوتيوب...")
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"   ⬆️  {int(status.progress() * 100)}%")

        video_id = response.get("id")
        print(f"   ✅ نُشر على يوتيوب: https://youtube.com/watch?v={video_id}")
        return video_id

    except Exception as e:
        print(f"   ❌ فشل النشر على يوتيوب: {e}")
        return None

# ══════════════════════════════════════════════
#  🗑️  تنظيف
# ══════════════════════════════════════════════
def cleanup_temp():
    for f in os.listdir(OUTPUT_DIR):
        if f.startswith("tmp_"):
            try:
                os.remove(os.path.join(OUTPUT_DIR, f))
            except Exception:
                pass

# ══════════════════════════════════════════════
#  🚀 AUTO RUN
# ══════════════════════════════════════════════
def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("=" * 55)
    print("🤖 مولّد قصص الفيديو — v3")
    print("=" * 55)

    client    = Groq(api_key=GROQ_API_KEY)
    history   = load_history()
    idea      = generate_idea(client, history)
    seed      = random.randint(1000, 99999)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    idea_slug = hashlib.md5(idea.encode()).hexdigest()[:6]
    out_name  = f"story_{timestamp}_{idea_slug}.mp4"

    print(f"🎲 الفكرة  : {idea}")
    print(f"🔑 Seed    : {seed}")
    print(f"🎞️  المشاهد : {SCENES_COUNT}")
    print(f"📁 الملف   : {out_name}\n")

    raw    = generate_story(idea, client)
    scenes = parse_story(raw, idea)
    print(f"📋 المشاهد: {len(scenes)}\n")

    print("⚙️  جاري المعالجة...")
    for i, scene in enumerate(scenes, start=1):
        img_path               = generate_image(scene["image_prompt"], i, seed)
        scene["subtitle_path"] = add_subtitle(img_path, scene["text"], i)
        scene["audio_path"]    = generate_audio(scene["text"], i)
        print(f"   ✅ مشهد {i}/{len(scenes)} جاهز")

    video_path = create_video(scenes, out_name)
    cleanup_temp()

    # ── نشر يوتيوب ──
    metadata   = {
        "title"      : f"قصة: {idea}",
        "description": (
            f"قصة قصيرة مولّدة بالذكاء الاصطناعي عن: {idea}\n\n"
            f"#قصص #ذكاء_اصطناعي #عربي #قصص_قصيرة"
        ),
        "tags"       : ["قصص", "ذكاء اصطناعي", "عربي", "قصص قصيرة"],
        "category"   : "Entertainment",
    }
    youtube_id = upload_to_youtube(video_path, metadata)

    # ── حفظ السجل ──
    history["videos"].append({
        "file"      : out_name,
        "idea"      : idea,
        "created_at": timestamp,
        "seed"      : seed,
        "published" : {
            "youtube"  : youtube_id,
            "tiktok"   : None,
            "instagram": None,
        },
        "metadata": metadata,
    })
    save_history(history)

    print("\n" + "=" * 55)
    print(f"🎉 اكتمل!")
    print(f"📁 الفيديو  : {video_path}")
    if youtube_id:
        print(f"📺 يوتيوب  : https://youtube.com/watch?v={youtube_id}")
    print(f"📊 إجمالي  : {len(history['videos'])} فيديو")
    print("=" * 55)
    return video_path

if __name__ == "__main__":
    run()
