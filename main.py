import os
import io
import time
import telebot
from telebot import types
import requests
import urllib3

urllib3.disable_warnings()

# ===== قراءة التوكن =====
BOT_TOKEN = os.getenv("6198804155:AAF5Zj-co6guQ6s2bW5hMTvFga8CFRi0WqA", "").strip()
if not BOT_TOKEN:
    try:
        from config import BOT_TOKEN as CFG_TOKEN
        BOT_TOKEN = CFG_TOKEN.strip()
    except Exception:
        BOT_TOKEN = ""

if not BOT_TOKEN:
    raise SystemExit("❌ ضع التوكن في BOT_TOKEN أو config.py")

bot = telebot.TeleBot(BOT_TOKEN)

# ===== توكن Google (نفس الطريقة القديمة) =====
def get_token():
    headers = {
        'Content-Type': 'application/json',
        'X-Android-Package': 'com.photoroom.app',
        'X-Android-Cert': '0424A4898A4B33940D8BF16E44251B876E97F8D0',
        'Accept-Language': 'en-US',
        'X-Client-Version': 'Android/Fallback/X23002000/FirebaseCore-Android',
        'X-Firebase-GMPID': '1:456289768976:android:30c90b24b80bc2d1bfdc95',
        'X-Firebase-Client': 'H4sIAAAAAAAAAKtWykhNLCpJSk0sKVayio7VUSpLLSrOzM9TslIyUqoFAFyivEQfAAAA',
        'X-Firebase-AppCheck': 'eyJlcnJvciI6IlVOS05PV05fRVJST1IifQ==',
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12)',
        'Host': 'www.googleapis.com',
    }
    params = {'key': 'AIzaSyAJGrgbFGB_-h8V2oJLr4b-_ipetqM0duU'}
    js = {'clientType': 'CLIENT_TYPE_ANDROID'}
    r = requests.post(
        'https://www.googleapis.com/identitytoolkit/v3/relyingparty/signupNewUser',
        headers=headers, params=params, json=js, timeout=30
    ).json()
    return r["idToken"]

# ===== دالة تحسين الصورة =====
def enhance_image(image_bytes, filename="image.jpg"):
    """
    ترسل الصورة لـ Photoroom وتجيب نسخة محسّنة/مكبرة.
    نجرّب عدة endpoints بالترتيب.
    """
    token = get_token()

    headers = {
        'Authorization': token,
        'Pr-App-Version': '2025.47.03 (2180)',
        'Pr-Platform': 'android',
        'User-Agent': 'okhttp/4.12.0',
        'Accept': 'application/json',
    }

    files = {'imageFile': (filename, image_bytes, 'image/jpeg')}

    # نحاول على endpoints مختلفة
    endpoints = [
        "https://serverless-api.photoroom.com/v2/ai-tools/upscale",
        "https://serverless-api.photoroom.com/v1/upscale",
        "https://serverless-api.photoroom.com/v2/upscale",
    ]

    last_error = None

    for url in endpoints:
        try:
            resp = requests.post(
                url,
                headers=headers,
                files=files,
                data={'scale': '2', 'mode': 'upscale'},
                verify=False,
                timeout=180
            )

            if resp.status_code == 200:
                # نحاول نستخرج رابط الصورة من الرد
                try:
                    data = resp.json()
                except Exception:
                    # إذا الرد مو JSON، يمكن يكون صورة مباشرة
                    if resp.content and len(resp.content) > 1000:
                        return ("bytes", resp.content)
                    last_error = f"رد غير متوقع من {url}"
                    continue

                # دوّر عن رابط الصورة في الرد
                img_url = _extract_url(data)
                if img_url:
                    return ("url", img_url)
                else:
                    last_error = f"ما لقى رابط بالرد: {str(data)[:200]}"
                    continue
            else:
                last_error = f"{url} → HTTP {resp.status_code}: {resp.text[:150]}"
                continue

        except Exception as e:
            last_error = f"{url} → {e}"
            continue

    raise Exception(last_error or "كل الـ endpoints فشلت")

def _extract_url(obj):
    """يبحث عن أي رابط صورة داخل الرد (JSON متداخل)"""
    if isinstance(obj, str):
        if obj.startswith("http") and any(x in obj.lower() for x in ['.png', '.jpg', '.jpeg', 'image', 'result']):
            return obj
        return None
    if isinstance(obj, dict):
        # أولوية لمفاتيح معروفة
        for key in ['url', 'imageUrl', 'image_url', 'result', 'output', 'upscaledUrl', 'outputUrl']:
            if key in obj:
                v = _extract_url(obj[key])
                if v:
                    return v
        for v in obj.values():
            r = _extract_url(v)
            if r:
                return r
    if isinstance(obj, list):
        for v in obj:
            r = _extract_url(v)
            if r:
                return r
    return None

# ===== /start =====
@bot.message_handler(commands=['start'])
def start(msg):
    text = (
        "هلا بيك حبي 🌟\n\n"
        "هذا بوت *يوضّح الصور* ويطلعها بجودة أعلى 🔍✨\n\n"
        "طريقة الاستخدام:\n"
        "1- دز الصورة (كتحويل لصورة أو كملف)\n"
        "2- انتظر ثواني…\n"
        "3- البوت يرجعلك الصورة موضّحة بجودة أعلى 📥\n\n"
        "📌 ملاحظات:\n"
        "• خلي الصورة واضحة نسبياً حتى تطلع أحسن نتيجة\n"
        "• الحد الأقصى للصورة 20MB"
    )
    bot.send_message(msg.chat.id, text, parse_mode="Markdown")

# ===== استقبال الصور =====
@bot.message_handler(content_types=['photo'])
def handle_photo(msg):
    uid = msg.from_user.id

    # نجيب أكبر حجم
    file_id = msg.photo[-1].file_id
    _process_image(uid, file_id, "image.jpg")

@bot.message_handler(content_types=['document'])
def handle_document(msg):
    uid = msg.from_user.id
    doc = msg.document

    if not doc.mime_type or not doc.mime_type.startswith("image/"):
        bot.reply_to(msg, "❌ هذا مو ملف صورة. دز صورة بصيغة JPG أو PNG.")
        return

    ext = "png" if "png" in doc.mime_type else "jpg"
    _process_image(uid, doc.file_id, f"image.{ext}")

def _process_image(uid, file_id, filename):
    # 1) رسالة انتظار
    wait_msg = bot.send_message(uid, "⏳ ثواني… دا نوضّح صورتك، انتظر شوي 🔍")

    # 2) تنزيل الصورة من تيليكرام
    try:
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)
    except Exception as e:
        bot.edit_message_text(f"❌ ما كدرت أنزل الصورة: {e}", uid, wait_msg.message_id)
        return

    # 3) تحسين الصورة
    try:
        kind, result = enhance_image(downloaded, filename)
    except Exception as e:
        bot.edit_message_text(
            f"❌ صار خطأ بالتحسين:\n`{str(e)[:300]}`",
            uid, wait_msg.message_id, parse_mode="Markdown"
        )
        return

    # 4) إرسال النتيجة
    try:
        if kind == "url":
            # رابط صورة
            img_resp = requests.get(result, timeout=90, verify=False)
            img_resp.raise_for_status()
            img_bytes = img_resp.content
        else:
            img_bytes = result

        # نرسلها كصورة معاينة
        bot.send_photo(uid, img_bytes, caption="✅ هاي صورتك الموضّحة ✨")

        # ونرسلها كملف بجودة كاملة
        bot.send_document(
            uid,
            img_bytes,
            visible_file_name="enhanced.png",
            caption="📥 نسخة كاملة بدون ضغط"
        )

        bot.delete_message(uid, wait_msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ تعذّر إرسال الصورة: {e}", uid, wait_msg.message_id)

# ===== رسائل أخرى =====
@bot.message_handler(content_types=['text'])
def fallback(msg):
    bot.reply_to(msg, "📸 دز لي صورة وأنا أوضّحها لك.")

# ===== تشغيل =====
print("Bot is running…")
bot.infinity_polling()
