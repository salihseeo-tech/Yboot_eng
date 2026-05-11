# 🎬 مولّد قصص الفيديو العربي التلقائي

يولّد قصة عربية كل 6 ساعات وينشرها على يوتيوب تلقائياً.

---

## 🗂️ هيكل المشروع

```
├── main.py                    ← الكود الرئيسي
├── get_youtube_token.py       ← لتوليد YouTube credentials (مرة واحدة)
├── requirements.txt           ← المكتبات
├── .gitignore
└── .github/
    └── workflows/
        └── generate.yml       ← GitHub Actions (كل 2 ساعات)
```

---

## 🚀 خطوات الإعداد

### 1. GitHub Secrets
روح: **Settings → Secrets and variables → Actions → New repository secret**

أضف هذين السكريتس:

| الاسم | القيمة |
|-------|--------|
| `GROQ_API_KEY` | مفتاحك من console.groq.com |
| `YOUTUBE_CREDENTIALS_JSON` | JSON من الخطوة التالية |

---

### 2. YouTube Credentials (مرة وحدة على جهازك)

```bash
# ثبّت المكتبات
pip install -r requirements.txt

# حمّل client_secrets.json من Google Cloud Console
# ضعه في نفس المجلد

# شغّل
python get_youtube_token.py
```

سيفتح المتصفح، سجّل دخول وأعط الصلاحيات.
بعدها انسخ محتوى `youtube_credentials.json` وضعه في GitHub Secret باسم `YOUTUBE_CREDENTIALS_JSON`

---

### 3. فعّل YouTube Data API v3
- روح: console.cloud.google.com
- APIs & Services → Library
- ابحث عن: YouTube Data API v3 → Enable

---

### 4. ارفع المشروع على GitHub

```bash
git init
git add .
git commit -m "first commit"
git remote add origin https://github.com/username/repo.git
git push -u origin main
```

---

## ⚙️ كيف يشتغل؟

```
كل 6 ساعات (أو يدوياً)
        ↓
Groq يولّد فكرة جديدة
        ↓
Groq يكتب قصة 8 مشاهد
        ↓
Pollinations يولّد 8 صور
        ↓
Edge TTS يقرأ القصة (صوت سعودي)
        ↓
MoviePy يجمع فيديو ~2.5 دقيقة
        ↓
ينشر تلقائياً على يوتيوب ✅
```

---

## 🔧 تشغيل محلي

```bash
# Windows
set GROQ_API_KEY=gsk_xxxx
set YOUTUBE_CREDENTIALS_JSON={"token":...}
python main.py

# Linux / Mac
export GROQ_API_KEY=gsk_xxxx
export YOUTUBE_CREDENTIALS_JSON='{"token":...}'
python main.py
```
