"""
🔑 get_youtube_token.py
شغّل هذا الملف مرة وحدة على جهازك لتحصل على YouTube credentials
بعدها انسخ الـ JSON وضعه في GitHub Secrets
"""

import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def main():
    print("=" * 50)
    print("🔑 YouTube Token Generator")
    print("=" * 50)

    # ── تأكد إن ملف الـ JSON موجود ──
    if not os.path.exists("client_secrets.json"):
        print("\n❌ ملف client_secrets.json غير موجود!")
        print("\nالخطوات:")
        print("1. روح: console.cloud.google.com")
        print("2. APIs & Services → Credentials")
        print("3. Create Credentials → OAuth Client ID → Desktop App")
        print("4. Download JSON وسميه: client_secrets.json")
        print("5. شغّل هذا الملف مرة ثانية")
        return

    # ── OAuth flow ──
    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
    creds = flow.run_local_server(port=0)

    # ── بناء الـ JSON اللي يدخل GitHub Secrets ──
    creds_dict = {
        "token"        : creds.token,
        "refresh_token": creds.refresh_token,
        "client_id"    : creds.client_id,
        "client_secret": creds.client_secret,
        "token_uri"    : creds.token_uri,
    }

    output = json.dumps(creds_dict, indent=2)

    # ── حفظ في ملف ──
    with open("youtube_credentials.json", "w") as f:
        f.write(output)

    print("\n✅ تم! الخطوات التالية:")
    print("\n1. افتح ملف: youtube_credentials.json")
    print("2. انسخ المحتوى كاملاً")
    print("3. روح GitHub → Settings → Secrets → Actions")
    print("4. New secret → الاسم: YOUTUBE_CREDENTIALS_JSON")
    print("5. الصق المحتوى → Save")
    print("\n⚠️  لا ترفع youtube_credentials.json على GitHub!")

if __name__ == "__main__":
    main()
