"""
🎬 Arabic Sports Video Generator — PROFESSIONAL MODE v1.0
Groq AI + Pollinations AI + Edge TTS + MoviePy v2
3 سلاسل رياضية احترافية:
  🧠 التحليل التكتيكي
  ⭐ نجوم وأساطير
  📊 أرقام وإحصاءات
"""

import os, sys, time, json, random, hashlib, requests, asyncio, edge_tts, re
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from groq import Groq

# ══════════════════════════════════════════════
#  ⚙️  الإعدادات
# ══════════════════════════════════════════════
GROQ_API_KEY      = os.environ.get("GROQ_API_KEY", "")
OUTPUT_DIR        = "output_sports"
HISTORY_FILE      = "history_sports.json"
VIDEO_W           = 1024
VIDEO_H           = 576
FPS               = 24
SCENES_COUNT      = 8
VOICE             = "ar-SA-HamedNeural"
SIMILARITY_THRESH = 0.55
MAX_IDEA_RETRIES  = 6

if not GROQ_API_KEY:
    print("❌ GROQ_API_KEY غير موجود في environment variables")
    sys.exit(1)

# ══════════════════════════════════════════════
#  📚 السلاسل الرياضية الثلاث
# ══════════════════════════════════════════════
SERIES = [
    {
        "id": "tactics",
        "name": "التحليل التكتيكي",
        "emoji": "🧠",
        "videos_per_cycle": 4,
        "idea_prompt": (
            "أنت محلل تكتيكي متخصص في كرة القدم. "
            "اقترح فكرة واحدة فقط لفيديو تحليل تكتيكي أو فني عميق يتعلق بكرة القدم العالمية. "
            "العنوان يكون احترافياً جذاباً لا يتجاوز 10 كلمات. "
            "أمثلة على المستوى المطلوب: "
            "'لماذا ضغط برشلونة العالي غيّر قواعد اللعبة'، "
            "'سر الخط الدفاعي العالي عند مانشستر سيتي'، "
            "'كيف يدمر كلوب الفرق بالكرة العالية والانتقال السريع'. "
            "يجب أن تكون مختلفة تماماً عن: {used}. "
            "أرجع العنوان فقط بدون أي نص إضافي."
        ),
        "story_prompt": (
            "أنت محلل تكتيكي متخصص، مستوى بي إن سبورتس. "
            "اكتب تحليلاً فنياً عميقاً واحترافياً باللغة العربية الفصحى عن: {idea}\n"
            "التحليل {n} مشاهد. كل مشهد يشرح جانباً تكتيكياً أو فنياً محدداً ودقيقاً.\n"
            "استخدم مصطلحات احترافية: الضغط الأعلى، البناء من الخلف، الكرة بين الخطوط، "
            "الجناح المقلوب، الجداري، التمركز، الانتقال الهجومي، الخط الدفاعي العالي.\n"
            "الأسلوب: تحليلي دقيق، موثوق، واضح، بدون كلام فارغ أو مبالغة.\n"
            "أرجع الرد بهذا الشكل بالضبط بدون أي نص إضافي:\n\n{template}"
        ),
        "image_style": (
            "professional football tactical broadcast, stadium cinematic lighting, "
            "tactical board overlay, ultra HD 4k, dramatic sports photography"
        ),
        "bar_color": (0, 20, 60),
        "text_color": (100, 180, 255, 255),
        "tags": ["تكتيك", "تحليل تكتيكي", "كرة القدم", "فن الكرة", "بيب جوارديولا", "كلوب"],
        "category_id": "17",
    },
    {
        "id": "legends",
        "name": "نجوم وأساطير",
        "emoji": "⭐",
        "videos_per_cycle": 4,
        "idea_prompt": (
            "أنت صحفي رياضي متخصص في كرة القدم. "
            "اقترح فكرة واحدة فقط لفيديو احترافي عن نجم أو أسطورة كروية — "
            "قصة، إنجاز، مقارنة، أو جانب غير معروف من مسيرته. "
            "العنوان جذاب لا يتجاوز 10 كلمات. "
            "أمثلة: "
            "'رونالدو والعقلية التي لا يملكها أحد في تاريخ الكرة'، "
            "'مسيرة زيدان: من مارسيليا إلى قمة العالم'، "
            "'لماذا كان رونالدينيو ظاهرة لن تتكرر أبداً'. "
            "يجب أن تكون مختلفة تماماً عن: {used}. "
            "أرجع العنوان فقط بدون أي نص إضافي."
        ),
        "story_prompt": (
            "أنت صحفي رياضي محترف على مستوى ESPN أو بي إن سبورتس. "
            "اكتب تقريراً صحفياً سردياً احترافياً باللغة العربية الفصحى عن: {idea}\n"
            "التقرير {n} مشاهد. كل مشهد يسرد جانباً حقيقياً ومثيراً من القصة.\n"
            "الأسلوب: سردي درامي موثوق، استند على حقائق حقيقية، "
            "ابدأ بمشهد يشد الانتباه فوراً، وانهِ بتقييم نقدي أو إرث اللاعب.\n"
            "لا مبالغة ولا معلومات وهمية — الاحترافية أولاً.\n"
            "أرجع الرد بهذا الشكل بالضبط بدون أي نص إضافي:\n\n{template}"
        ),
        "image_style": (
            "professional football player portrait, stadium atmosphere, "
            "dramatic cinematic sports photography, golden hour lighting, 4k ultra HD"
        ),
        "bar_color": (40, 20, 0),
        "text_color": (255, 210, 80, 255),
        "tags": ["نجوم الكرة", "أساطير كرة القدم", "رونالدو", "ميسي", "زيدان", "مسيرة"],
        "category_id": "17",
    },
    {
        "id": "stats",
        "name": "أرقام وإحصاءات",
        "emoji": "📊",
        "videos_per_cycle": 4,
        "idea_prompt": (
            "أنت محلل إحصائي رياضي متخصص. "
            "اقترح فكرة واحدة فقط لفيديو يقدم أرقاماً وإحصاءات مذهلة في كرة القدم. "
            "العنوان احترافي جذاب لا يتجاوز 10 كلمات. "
            "أمثلة: "
            "'الأرقام التي تثبت أن ميسي لن يتكرر أبداً'، "
            "'أكثر 10 هدافين في تاريخ دوري أبطال أوروبا'، "
            "'إحصاءات مجنونة لا تعرفها عن كأس العالم'. "
            "يجب أن تكون مختلفة تماماً عن: {used}. "
            "أرجع العنوان فقط بدون أي نص إضافي."
        ),
        "story_prompt": (
            "أنت محلل إحصائي رياضي متخصص. "
            "اكتب محتوى إحصائياً احترافياً ومذهلاً باللغة العربية الفصحى عن: {idea}\n"
            "المحتوى {n} مشاهد. كل مشهد يقدم رقماً أو إحصائية حقيقية ومثيرة مع سياقها.\n"
            "الأسلوب: دقيق، موثوق، قدّم الأرقام بطريقة مشوقة تجعل المشاهد يتفاجأ.\n"
            "استخدم مقارنات لتوضيح ضخامة الرقم — مثلاً: 'هذا يعادل...' أو 'لم يفعل هذا سوى...'.\n"
            "لا تخترع أرقاماً — استخدم أرقاماً حقيقية ومعروفة.\n"
            "أرجع الرد بهذا الشكل بالضبط بدون أي نص إضافي:\n\n{template}"
        ),
        "image_style": (
            "professional sports statistics infographic, football data visualization, "
            "cinematic broadcast style, dramatic neon lighting, 4k ultra HD"
        ),
        "bar_color": (0, 40, 20),
        "text_color": (100, 255, 160, 255),
        "tags": ["إحصاءات", "أرقام كرة القدم", "ميسي", "رونالدو", "دوري أبطال أوروبا", "كأس العالم"],
        "category_id": "17",
    },
]

# ══════════════════════════════════════════════
#  🔍 فحص التكرار — 3 طبقات
# ══════════════════════════════════════════════
def normalize(text):
    text = re.sub(r'[\u064B-\u065F]', '', text)
    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip().lower()
    return text

def jaccard_similarity(a, b):
    wa = set(normalize(a).split())
    wb = set(normalize(b).split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)

def is_duplicate(new_idea, used_ideas, threshold=SIMILARITY_THRESH):
    new_norm     = normalize(new_idea)
    new_keywords = set(list(new_norm.split())[:3])
    for old in used_ideas:
        old_norm = normalize(old)
        if new_norm == old_norm:
            return True, old, 1.0
        score = jaccard_similarity(new_idea, old)
        if score >= threshold:
            return True, old, score
        old_keywords = set(list(old_norm.split())[:3])
        kw_score = len(new_keywords & old_keywords) / max(len(new_keywords | old_keywords), 1)
        if kw_score >= 0.7:
            return True, old, kw_score
    return False, None, 0.0

# ══════════════════════════════════════════════
#  📋 السجل
# ══════════════════════════════════════════════
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
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
#  🔄 تدوير السلاسل
# ══════════════════════════════════════════════
def get_current_series(history):
    idx    = history.get("current_series_index", 0)
    count  = history.get("current_series_count", 0)
    series = SERIES[idx % len(SERIES)]
    if count >= series["videos_per_cycle"]:
        idx    = (idx + 1) % len(SERIES)
        count  = 0
        series = SERIES[idx]
        print(f"\n🔄 انتقلنا إلى سلسلة جديدة: {series['emoji']} {series['name']}\n")
    history["current_series_index"] = idx
    history["current_series_count"] = count + 1
    return series

# ══════════════════════════════════════════════
#  🤖 Groq — فكرة مع فحص تكرار عميق
# ══════════════════════════════════════════════
def generate_idea(client, history, series):
    used      = history.get("used_ideas", [])
    used_list = ", ".join(used[-40:]) if used else "لا يوجد"

    for attempt in range(1, MAX_IDEA_RETRIES + 1):
        prompt = series["idea_prompt"].format(used=used_list)
        resp   = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=min(0.90 + attempt * 0.03, 1.3),
        )
        idea = resp.choices[0].message.content.strip().strip('"\'').strip("-").strip()

        dup, matched, score = is_duplicate(idea, used)
        if dup:
            print(f"   ⚠️  محاولة {attempt}: مشابه ({score:.0%}) لـ '{matched}' — أعيد")
            used_list = ", ".join(used[-40:]) + f", {idea}"
            continue

        print(f"   ✅ فكرة فريدة (محاولة {attempt}): {idea}")
        history["used_ideas"].append(idea)
        return idea

    fallback = f"{idea} {datetime.now().strftime('%H%M')}"
    print(f"   ⚠️  fallback: {fallback}")
    history["used_ideas"].append(fallback)
    return fallback

# ══════════════════════════════════════════════
#  🤖 Groq — المحتوى
# ══════════════════════════════════════════════
def build_scenes_template():
    t = ""
    for i in range(1, SCENES_COUNT + 1):
        t += f"مشهد {i}: [النص العربي الاحترافي — جملة أو جملتان]\nصورة {i}: [وصف إنجليزي سينمائي]\n\n"
    return t

def generate_story(idea, client, series):
    print("   جاري كتابة المحتوى الاحترافي...")
    prompt = series["story_prompt"].format(
        idea=idea,
        n=SCENES_COUNT,
        template=build_scenes_template()
    )
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.75,  # أقل عشوائية = أكثر احترافية
    )
    print("   ✅ المحتوى جاهز")
    return resp.choices[0].message.content

def parse_story(raw, idea, series):
    scenes, current = [], {}
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r'^مشهد\s*\d+\s*:', line):
            if current:
                scenes.append(current)
            current = {"text": line.split(":", 1)[1].strip()}
        elif re.match(r'^صورة\s*\d+\s*:', line):
            current["image_prompt"] = line.split(":", 1)[1].strip()
    if current:
        scenes.append(current)

    scenes = [s for s in scenes if "text" in s and "image_prompt" in s]

    if not scenes:
        print("⚠️  فشل التحليل، fallback...")
        fallback = {
            "tactics": [
                ("يبدأ التحليل من الطريقة التي يضغط بها الفريق على الكرة.",           "football tactical pressing high line cinematic"),
                ("الخط الدفاعي العالي يخلق مساحة خلف المهاجمين.",                    "defensive high line football stadium dramatic"),
                ("البناء من الخلف يتطلب حارساً يشارك في اللعب.",                     "goalkeeper ball playing build-up cinematic"),
                ("الكرة بين الخطوط هي أخطر لحظة دفاعياً.",                          "football between the lines tactical broadcast"),
                ("الجناح المقلوب يخلق فرص التسديد من داخل القدم.",                   "inverted winger football tactical 4k"),
                ("الانتقال السريع من دفاع لهجوم يرهق الخصم.",                        "fast counter attack football cinematic"),
                ("الضغط الأعلى يسبب أخطاء في منطقة الخصم.",                         "gegenpressing football high press broadcast"),
                ("هذا التكتيك غيّر وجه كرة القدم الحديثة إلى الأبد.",               "modern football tactics evolution cinematic"),
            ],
            "legends": [
                ("بدأت رحلته من حي فقير لم يكن أحد يتوقع منه شيئاً.",               "football legend childhood humble beginnings cinematic"),
                ("في أولى مبارياته الاحترافية، أثبت أنه مختلف.",                    "young football star debut stadium dramatic"),
                ("كان تدريبه يختلف عن كل لاعب في الفريق.",                          "football legend training session cinematic"),
                ("جاء اللقب الأول بعد سنوات من التضحية والعمل.",                    "football champion trophy lift stadium"),
                ("اللحظة الفارقة التي غيّرت مسيرته إلى الأبد.",                    "football legend career turning point dramatic"),
                ("الإصابة كادت توقف كل شيء، لكنه عاد أقوى.",                       "football comeback from injury cinematic"),
                ("رقمه القياسي لا يزال شاهداً على عظمته.",                          "football record celebration stadium cinematic"),
                ("هذا الإرث لن يمحوه الزمن أبداً.",                                "football legend legacy stadium golden hour"),
            ],
            "stats": [
                ("هذا الرقم يجعلك تدرك حجم العظمة الحقيقية.",                      "football statistics infographic dramatic neon"),
                ("في كل 90 دقيقة، كان يصنع الفارق.",                               "football stats per 90 minutes broadcast"),
                ("لا أحد في التاريخ سجّل هذا الرقم من قبله.",                      "football record goals all time cinematic"),
                ("المقارنة مع أساطير الماضي تجعل الرقم أكثر إدهاشاً.",             "football statistics comparison broadcast"),
                ("في البطولات الكبرى، الرقم يتضاعف.",                              "football champions league statistics dramatic"),
                ("حتى خصومه اعترفوا بأن هذه الأرقام فوق العادة.",                  "football rivals admitting greatness cinematic"),
                ("هذه الإحصاءات تبقى ثابتة حتى بعد عشر سنوات.",                   "football legacy statistics timeline"),
                ("وهذا ما يجعله الأفضل في التاريخ بكل موضوعية.",                   "football goat debate statistics cinematic"),
            ],
        }
        base   = fallback.get(series["id"], fallback["tactics"])
        scenes = [{"text": t, "image_prompt": f"{idea}, {p}"} for t, p in base]

    return scenes[:SCENES_COUNT]

# ══════════════════════════════════════════════
#  🖼️  Pollinations — صور بستايل كل سلسلة
# ══════════════════════════════════════════════
def generate_image(prompt, index, seed, series):
    print(f"   🖼️  صورة {index}/{SCENES_COUNT}...")
    enhanced = f"{prompt}, {series['image_style']}"
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

    colors = {
        "tactics": ["#000c1a", "#001433", "#001f4d", "#000a14", "#00152b", "#001a3d", "#000f24", "#00193a"],
        "legends": ["#1a0e00", "#2b1800", "#3d2200", "#140a00", "#221100", "#331900", "#1f0d00", "#290f00"],
        "stats":   ["#001a0d", "#002b14", "#003d1f", "#00140a", "#001f0f", "#002e17", "#001a0c", "#002614"],
    }
    color_list = colors.get(series["id"], colors["tactics"])
    img  = Image.new("RGB", (VIDEO_W, VIDEO_H), color_list[index % len(color_list)])
    path = os.path.join(OUTPUT_DIR, f"tmp_scene_{index}.jpg")
    img.save(path)
    return path

# ══════════════════════════════════════════════
#  🖊️  Pillow — subtitle احترافي
# ══════════════════════════════════════════════
def load_font(size):
    for fp in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size=size)
            except Exception:
                pass
    return ImageFont.load_default()

def wrap_text(text, max_chars=50):
    words = text.split()
    lines, line = [], ""
    for w in words:
        if len(line) + len(w) + 1 <= max_chars:
            line = f"{line} {w}".strip()
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines[:3]

def add_subtitle(image_path, text, index, series):
    img     = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    bc    = series["bar_color"]
    bar_h = 160

    # تدرج الشريط
    for y in range(bar_h):
        alpha = int(220 * (1 - y / bar_h * 0.2))
        draw.rectangle(
            [(0, img.height - bar_h + y), (img.width, img.height - bar_h + y + 1)],
            fill=(bc[0], bc[1], bc[2], alpha)
        )

    # شارة السلسلة (أعلى يسار)
    badge_font = load_font(19)
    badge_text = f"{series['emoji']}  {series['name']}"
    draw.rectangle([(12, 12), (260, 44)], fill=(0, 0, 0, 180))
    draw.text((20, 16), badge_text, font=badge_font, fill=(255, 255, 255, 220))

    # خط فاصل فوق الشريط
    draw.rectangle(
        [(0, img.height - bar_h), (img.width, img.height - bar_h + 3)],
        fill=(series["text_color"][0], series["text_color"][1], series["text_color"][2], 200)
    )

    font  = load_font(31)
    tc    = series["text_color"]
    lines = wrap_text(text)

    y = img.height - bar_h + 18
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        tw = bb[2] - bb[0]
        x  = (img.width - tw) // 2
        # ظل
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 220))
        # نص
        draw.text((x, y), line, font=font, fill=tc)
        y += 46

    merged = Image.alpha_composite(img, overlay).convert("RGB")
    out    = os.path.join(OUTPUT_DIR, f"tmp_sub_{index}.jpg")
    merged.save(out, quality=95)
    return out

# ══════════════════════════════════════════════
#  🔊 Edge TTS
# ══════════════════════════════════════════════
def generate_audio(text, index):
    path = os.path.join(OUTPUT_DIR, f"tmp_audio_{index}.mp3")
    async def _speak():
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(path)
    asyncio.run(_speak())
    return path

# ══════════════════════════════════════════════
#  🎬 MoviePy v2
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

    for scene in scenes_data:
        if not os.path.exists(scene["audio_path"]):
            print(f"   ⚠️  ملف صوت مفقود — تخطي")
            continue
        audio = AudioFileClip(scene["audio_path"])
        if audio.duration < 0.1:
            audio.close()
            continue
        duration = audio.duration + 0.8
        clip = (
            ImageClip(scene["subtitle_path"], duration=duration)
            .with_audio(audio)
            .with_start(start)
            .with_effects([FadeIn(FADE), FadeOut(FADE)])
        )
        clips.append(clip)
        start += duration - FADE

    if not clips:
        print("❌ لا توجد مقاطع صالحة.")
        sys.exit(1)

    total    = start + clips[-1].duration
    final    = CompositeVideoClip(clips, size=(VIDEO_W, VIDEO_H)).with_duration(total)
    out_path = os.path.join(OUTPUT_DIR, output_name)
    final.write_videofile(out_path, fps=FPS, codec="libx264", audio_codec="aac", logger=None)
    return out_path

# ══════════════════════════════════════════════
#  📺 YouTube
# ══════════════════════════════════════════════
def upload_to_youtube(video_path, metadata):
    try:
        import google.oauth2.credentials
        import googleapiclient.discovery
        import googleapiclient.http

        creds_json = os.environ.get("YOUTUBE_CREDENTIALS_JSON", "")
        if not creds_json:
            print("⚠️  YOUTUBE_CREDENTIALS_JSON غير موجود — تخطي النشر")
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
                "categoryId" : metadata["category_id"],
            },
            "status": {"privacyStatus": "public"},
        }
        media    = googleapiclient.http.MediaFileUpload(
            video_path, mimetype="video/mp4", resumable=True, chunksize=1024*1024
        )
        request  = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = None
        print("📤 جاري الرفع على يوتيوب...")
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"   ⬆️  {int(status.progress() * 100)}%")
        video_id = response.get("id")
        print(f"   ✅ نُشر: https://youtube.com/watch?v={video_id}")
        return video_id
    except Exception as e:
        print(f"   ❌ فشل النشر: {e}")
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
#  🚀 التشغيل
# ══════════════════════════════════════════════
def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("=" * 55)
    print("⚽ مولّد المحتوى الرياضي الاحترافي — v1.0")
    print("=" * 55)

    client  = Groq(api_key=GROQ_API_KEY)
    history = load_history()

    series = get_current_series(history)
    print(f"📺 السلسلة   : {series['emoji']} {series['name']}")
    print(f"🔢 الفيديو   : {history['current_series_count']}/{series['videos_per_cycle']}")
    print(f"📦 أفكار محفوظة: {len(history.get('used_ideas', []))}\n")

    seed      = random.randint(1000, 99999)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("🧠 توليد فكرة فريدة...")
    idea      = generate_idea(client, history, series)
    idea_slug = hashlib.md5(idea.encode()).hexdigest()[:6]
    out_name  = f"{series['id']}_{timestamp}_{idea_slug}.mp4"

    print(f"🎲 الفكرة  : {idea}")
    print(f"🔑 Seed    : {seed}")
    print(f"🎞️  المشاهد : {SCENES_COUNT}")
    print(f"📁 الملف   : {out_name}\n")

    raw    = generate_story(idea, client, series)
    scenes = parse_story(raw, idea, series)
    print(f"📋 المشاهد: {len(scenes)}\n")

    print("⚙️  معالجة المشاهد...")
    for i, scene in enumerate(scenes, start=1):
        img_path               = generate_image(scene["image_prompt"], i, seed, series)
        scene["subtitle_path"] = add_subtitle(img_path, scene["text"], i, series)
        scene["audio_path"]    = generate_audio(scene["text"], i)
        print(f"   ✅ مشهد {i}/{len(scenes)} جاهز")

    video_path = create_video(scenes, out_name)
    cleanup_temp()

    metadata = {
        "title"      : f"{series['emoji']} {idea}",
        "description": (
            f"{series['name']} | {idea}\n\n"
            f"اشترك في القناة للمزيد من المحتوى الرياضي الاحترافي 🔔\n\n"
            f"#{' #'.join(series['tags'])}"
        ),
        "tags"       : series["tags"],
        "category_id": series["category_id"],
    }
    youtube_id = upload_to_youtube(video_path, metadata)

    history["series_tracker"][series["id"]] = history["series_tracker"].get(series["id"], 0) + 1
    history["videos"].append({
        "file"      : out_name,
        "idea"      : idea,
        "series"    : series["id"],
        "created_at": timestamp,
        "seed"      : seed,
        "published" : {"youtube": youtube_id},
        "metadata"  : metadata,
    })
    save_history(history)

    tracker = history["series_tracker"]
    print("\n" + "=" * 55)
    print("🎉 اكتمل!")
    print(f"📁 الفيديو  : {video_path}")
    if youtube_id:
        print(f"📺 يوتيوب  : https://youtube.com/watch?v={youtube_id}")
    print(f"\n📊 إحصاءات السلاسل:")
    for s in SERIES:
        print(f"   {s['emoji']} {s['name']}: {tracker.get(s['id'], 0)} فيديو")
    print(f"\n📦 الإجمالي     : {len(history['videos'])} فيديو")
    print(f"🧠 أفكار محفوظة : {len(history['used_ideas'])}")
    print("=" * 55)
    return video_path

if __name__ == "__main__":
    run()
