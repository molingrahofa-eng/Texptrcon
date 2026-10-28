import os
import io
import telebot
from telebot import types
import requests
import base64

# ===== التوكن الخاص ببوت التليكرام =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "6198804155:AAF5Zj-co6guQ6s2bW5hMTvFga8CFRi0WqA").strip()
if not BOT_TOKEN:
    try:
        from config import BOT_TOKEN as CFG_TOKEN
        BOT_TOKEN = CFG_TOKEN.strip()
    except Exception:
        BOT_TOKEN = ""

if not BOT_TOKEN:
    raise SystemExit("❌ ضع توكن البوت في BOT_TOKEN أو config.py")

bot = telebot.TeleBot(BOT_TOKEN)

# ===== مفتاح API لخدمة تحسين الصور (Venice.ai أو DeepAI) =====
# احصل على مفتاح مجاني من: https://venice.ai/settings/api
# أو من DeepAI: https://deepai.org/dashboard/profile
IMAGE_API_KEY = os.getenv("IMAGE_API_KEY", "").strip()

# اختر الخدمة: "venice" أو "deepai"
API_SERVICE = "venice" 

def upscale_image_venice(image_bytes):
    """تحسين الصورة باستخدام Venice.ai"""
    if not IMAGE_API_KEY:
        raise Exception("مفتاح API غير موجود. ضعه في IMAGE_API_KEY.")
    
    # Venice تتطلب الصورة بصيغة base64
    img_b64 = base64.b64encode(image_bytes).decode("utf-8")
    
    headers = {
        "Authorization": f"Bearer {IMAGE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "image": img_b64,
        "scale": 2.0  # يمكنك تغييرها إلى 4.0
    }
    
    resp = requests.post(
        "https://api.venice.ai/api/v1/image/upscale",
        headers=headers,
        json=payload,
        timeout=120
    )
    
    if resp.status_code != 200:
        raise Exception(f"Venice API error: {resp.status_code} - {resp.text[:200]}")
    
    # Venice ترجع الصورة كبيانات ثنائية (binary)
    return resp.content

def upscale_image_deepai(image_bytes):
    """تحسين الصورة باستخدام DeepAI (بديل)"""
    if not IMAGE_API_KEY:
        raise Exception("مفتاح API غير موجود. ضعه في IMAGE_API_KEY.")
    
    files = {'image': ('image.jpg', image_bytes, 'image/jpeg')}
    headers = {"api-key": IMAGE_API_KEY}
    
    resp = requests.post(
        "https://api.deepai.org/api/torch-srgan",
        files=files,
        headers=headers,
        timeout=120
    )
    
    if resp.status_code != 200:
        raise Exception(f"DeepAI error: {resp.status_code} - {resp.text[:200]}")
    
    data = resp.json()
    output_url = data.get("output_url")
    if not output_url:
        raise Exception("لم يتم استلام رابط الصورة من DeepAI")
    
    # تنزيل الصورة المحسنة
    img_resp = requests.get(output_url, timeout=60)
    return img_resp.content

@bot.message_handler(commands=['start'])
def start(msg):
    text = (
        "هلا بيك حبي 🌟\n\n"
        "هذا بوت *يوضّح الصور* ويرفع جودتها 🔍✨\n\n"
        "فقط دز الصورة (كتحويل أو كملف) وانتظر النتيجة.\n\n"
        "📌 الحد الأقصى 20MB."
    )
    bot.send_message(msg.chat.id, text, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def handle_photo(msg):
    # نجيب أعلى دقة للصورة
    file_id = msg.photo[-1].file_id
    _process_image(msg.chat.id, file_id, "image.jpg")

@bot.message_handler(content_types=['document'])
def handle_document(msg):
    doc = msg.document
    if not doc.mime_type or not doc.mime_type.startswith("image/"):
        bot.reply_to(msg, "❌ هذا مو ملف صورة. دز صورة JPG أو PNG.")
        return
    ext = "png" if "png" in doc.mime_type else "jpg"
    _process_image(msg.chat.id, doc.file_id, f"image.{ext}")

def _process_image(chat_id, file_id, filename):
    wait_msg = bot.send_message(chat_id, "⏳ جاري تحسين الصورة... انتظر شوي 🔍")
    
    try:
        # تنزيل الصورة من تيليكرام
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        # اختيار الخدمة
        if API_SERVICE == "venice":
            enhanced_bytes = upscale_image_venice(downloaded)
        else:
            enhanced_bytes = upscale_image_deepai(downloaded)
        
        # إرسال النتيجة
        bot.send_photo(chat_id, enhanced_bytes, caption="✅ هذه صورتك الموضّحة ✨")
        bot.send_document(
            chat_id, 
            enhanced_bytes, 
            visible_file_name="enhanced.png",
            caption="📥 نسخة كاملة بدون ضغط"
        )
        bot.delete_message(chat_id, wait_msg.message_id)
        
    except Exception as e:
        bot.edit_message_text(
            f"❌ صار خطأ:\n`{str(e)[:300]}`", 
            chat_id, 
            wait_msg.message_id, 
            parse_mode="Markdown"
        )

@bot.message_handler(content_types=['text'])
def fallback(msg):
    bot.reply_to(msg, "📸 دز لي صورة وأنا أوضّحها لك.")

print("Bot is running…")
bot.infinity_polling()
