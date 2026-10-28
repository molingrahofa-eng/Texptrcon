import telebot
from telebot import types
import requests
import urllib3

urllib3.disable_warnings()

# ===== التوكن =====
BOT_TOKEN = input("6198804155:AAF5Zj-co6guQ6s2bW5hMTvFga8CFRi0WqA").strip()
bot = telebot.TeleBot(BOT_TOKEN)

# ===== الستايلات =====
STYLES = [
    ("diversity", "التنوع — Diversity"),
    ("hyper-realistic", "واقعي هواية — Hyper Realistic"),
    ("impressionist", "ستايل انطباعي — Impressionist"),
    ("low-poly", "ستايل خفيف التفاصيل — Low Poly"),
    ("isometric", "منظور أيزومتريك — Isometric"),
    ("cyberpunk", "سايبربنك — Cyberpunk"),
    ("baroque", "باروكي — Baroque"),
    ("abstract-expressionism", "مجرد تعبيري — Abstract Expressionism"),
    ("photorealistic-cgi", "CGI واقعي — Photorealistic CGI"),
    ("surrealist", "سيريالي — Surrealist")
]

# ===== المقاسات =====
SIZES = [
    ("SQUARE_HD", "مربع 1:1"),
    ("PORTRAIT_4_3", "طولي 3:4"),
    ("PORTRAIT_16_9", "طولي 9:16"),
    ("LANDSCAPE_4_3", "عرضي 4:3"),
    ("LANDSCAPE_16_9", "عرضي 16:9")
]

# ===== الحالة =====
user_state = {}
user_data = {}

# ===== التوكن من Google =====
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

# ===== توليد الصور =====
def generate_images(prompt, styleId, sizeId):
    token = get_token()
    headers = {
        'Host': 'serverless-api.photoroom.com',
        'Accept': 'text/event-stream',
        'Authorization': token,
        'Content-Type': 'application/json; charset=utf-8',
        'User-Agent': 'okhttp/4.12.0',
        'Pr-App-Version': '2025.47.03 (2180)',
        'Pr-Platform': 'android',
    }
    payload = {
        "userPrompt": prompt,
        "appId": "expert",
        "styleId": styleId,
        "sizeId": sizeId,
        "numberOfImages": 4
    }
    resp = requests.post(
        "https://serverless-api.photoroom.com/v2/ai-tools/generate-images",
        headers=headers, json=payload, stream=True, verify=False, timeout=120
    )
    bg, nobg = [], []
    for line in resp.iter_lines():
        if not line:
            continue
        l = line.decode()
        if '"eventType":"aiImageResult"' in l:
            s = l.find('"imageUrl":"') + 12
            e = l.find('"', s)
            bg.append(l[s:e])
        if '"eventType":"aiImageWithoutBackgroundResult"' in l:
            s = l.find('"imageUrl":"') + 12
            e = l.find('"', s)
            nobg.append(l[s:e])
    return bg, nobg

# ===== أزرار المطور =====
def dev_buttons(kb):
    kb.add(
        types.InlineKeyboardButton("👨‍💻 المطور", url="https://t.me/p7s7s"),
        types.InlineKeyboardButton("📢 قناة المطور", url="https://t.me/ZVBZBZB2")
    )
    return kb

# ===== إرسال الصور بجودة أصلية (بدون ضغط) =====
def send_images_hd(uid, urls, styleId, sizeId, prompt):
    """
    يبعت الصور كألبوم أول (سريع)،
    وبعدين يبعتها كملفات (document) حتى تكون بجودة أصلية بدون ضغط تليكرام.
    """
    total = len(urls)

    # 1) ألبوم سريع للمعاينة
    media = []
    for i, url in enumerate(urls[:10], 1):
        cap = (
            f"🖼 صورة {i}/{total}\n"
            f"🎨 الستايل: {styleId}\n"
            f"📐 القياس: {sizeId}\n"
            f"📝 {prompt[:80]}"
        )
        media.append(types.InputMediaPhoto(url, caption=cap))
    try:
        bot.send_media_group(uid, media)
    except Exception:
        pass  # إذا فشل، الملفات بالأسفل تكفي

    # 2) نسخة ملفات بدون ضغط (الجودة الأصلية)
    bot.send_message(uid, "📥 هاي نسخة كاملة بدون ضغط (جودة أصلية):")
    for i, url in enumerate(urls, 1):
        try:
            r = requests.get(url, timeout=90, verify=False)
            r.raise_for_status()
            bot.send_document(
                uid,
                r.content,
                visible_file_name=f"image_{i}.png",
                caption=f"🖼 صورة {i}/{total} — جودة كاملة"
            )
        except Exception as e:
            bot.send_message(uid, f"⚠️ تعذّر إرسال الصورة {i} كملف: {e}")

# ===== لوحة بعد النتيجة =====
def result_menu(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔁 إعادة توليد", callback_data="regen"),
        types.InlineKeyboardButton("🏠 رجوع", callback_data="home")
    )
    dev_buttons(kb)
    bot.send_message(uid, "خلصت الصور ✔️ شتريد تسوي هسه؟", reply_markup=kb)

# ===== /start =====
@bot.message_handler(commands=['start'])
def start(msg):
    text = (
        "هلا بيك حبي 🌟\n"
        "هذا بوت يصنع صور نار🔥 وبجودة قوية.\n\n"
        "طريقة الشغل:\n"
        "1- تختار ستايل الصورة\n"
        "2- تختار القياس\n"
        "3- تكتب البرومبت مالك\n"
        "وبعدها البوت يسويلك *٤ صور مرتبة* بجودة عالية 🤩\n\n"
        "اختار الستايل حتى نبدي:"
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    for st_id, st_name in STYLES:
        kb.add(types.InlineKeyboardButton(st_name, callback_data=f"style:{st_id}"))
    dev_buttons(kb)
    bot.send_message(msg.chat.id, text, reply_markup=kb, parse_mode="Markdown")

# ===== اختيار الستايل =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("style:"))
def choose_size(call):
    uid = call.from_user.id
    styleId = call.data.split(":")[1]
    user_data[uid] = {"styleId": styleId}

    kb = types.InlineKeyboardMarkup(row_width=2)
    for sz_id, sz_name in SIZES:
        kb.add(types.InlineKeyboardButton(sz_name, callback_data=f"size:{sz_id}"))
    dev_buttons(kb)

    bot.edit_message_text(
        "اختار القياس اللي يعجبك:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )

# ===== اختيار القياس =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("size:"))
def ask_prompt(call):
    uid = call.from_user.id
    sizeId = call.data.split(":")[1]
    user_data.setdefault(uid, {})["sizeId"] = sizeId
    user_state[uid] = "await_prompt"

    bot.edit_message_text(
        "دز البرومبت مال الصورة:",
        call.message.chat.id,
        call.message.message_id
    )

# ===== استقبال البرومبت =====
@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "await_prompt")
def handle_prompt(msg):
    uid = msg.from_user.id
    prompt = msg.text
    if not prompt:
        bot.send_message(uid, "اكتب وصف نصي للصورة 🙂")
        return

    user_data[uid]["prompt"] = prompt
    styleId = user_data[uid]["styleId"]
    sizeId = user_data[uid]["sizeId"]

    bot.send_message(uid, "ثواني حبي… دا نسويلك الصور ⏳🔥")

    try:
        bg, nobg = generate_images(prompt, styleId, sizeId)
    except Exception as e:
        bot.send_message(uid, f"صار خطأ بالتوليد 😢\n{e}")
        user_state.pop(uid, None)
        return

    if not bg:
        bot.send_message(uid, "ما رجعت ولا صورة 😢 جرّب برومبت ثاني.")
        user_state.pop(uid, None)
        return

    send_images_hd(uid, bg, styleId, sizeId, prompt)
    result_menu(uid)
    user_state.pop(uid, None)

# ===== رجوع =====
@bot.callback_query_handler(func=lambda c: c.data == "home")
def go_home(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    start(call.message)

# ===== إعادة توليد =====
@bot.callback_query_handler(func=lambda c: c.data == "regen")
def regenerate(call):
    uid = call.from_user.id
    d = user_data.get(uid)
    if not d or "prompt" not in d:
        bot.answer_callback_query(call.id, "ابدأ من /start")
        return

    bot.answer_callback_query(call.id, "دا نعيد التوليد… 🔄")

    try:
        bg, _ = generate_images(d["prompt"], d["styleId"], d["sizeId"])
    except Exception as e:
        bot.send_message(uid, f"صار خطأ: {e}")
        return

    if not bg:
        bot.send_message(uid, "ما رجعت صور 😢 جرّب مرة ثانية.")
        return

    send_images_hd(uid, bg, d["styleId"], d["sizeId"], d["prompt"])
    result_menu(uid)

# ===== تشغيل =====
print("Bot is running…")
bot.infinity_polling()
