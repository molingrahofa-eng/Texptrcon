import os
import sys
import json
import time
import random
import asyncio
import hashlib
import hmac
import uuid
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# ==========================================
# ⚙️ الإعدادات الأساسية
# ==========================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "6198804155:AAF5Zj-co6guQ6s2bW5hMTvFga8CFRi0WqA")
try:
    OWNER_ID = int(os.environ.get("OWNER_ID", "5952132218"))
except:
    OWNER_ID = 5952132218

keybytes = [0x35, 0x30, 0x1c, 0x2f, 0x2c, 0x2c, 0x28, 0x31, 0x35, 0x30, 0x1c, 0x2f, 0x2c, 0x2c, 0x28, 0x31]
secretkey = bytes([b ^ 0x43 for b in keybytes])
ENDPOINT = "https://api.tikspark.xyz/graphql"
DEFAULT_DEVINFO = '{"d":"61393235613366373261636533656632","n":"494e46494e495820496e66696e6978204c697465203330","o":"16","t":"d","v":"2.2.9","s":"0,0"}'
DEFAULT_CSRF = "1786692648457:b5fb61a1a92b2de8ffa0343c5d45ce9f1e578abb695cca7ab6659cfc29f85fe9"

DATA_FILE = "data.json"

USERS = {} 
CODES = {}
CHANNELS = []
USER_ACCOUNTS = {}

def save_data():
    data = {"users": USERS, "codes": CODES, "channels": CHANNELS, "accounts": USER_ACCOUNTS}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_data():
    global USERS, CODES, CHANNELS, USER_ACCOUNTS
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                USERS = data.get("users", {})
                CODES = data.get("codes", {})
                CHANNELS = data.get("channels", [])
                USER_ACCOUNTS = data.get("accounts", {})
        except: pass

def get_user(uid):
    uid = str(uid)
    if uid not in USERS:
        USERS[uid] = {"exp": 0, "max_acc": 3, "blocked": False, "starts": 0, "speed": "normal", "work_hours": 16}
    return USERS[uid]

# ==========================================
# 🌐 الترجمات (مختصرة)
# ==========================================
T = {
    "menu": "🏠 *القائمة الرئيسية*\n\n👤 النشط: `{}` | ⭐ *{}*\n📋 الحسابات: *{}* من أصل *{}*\n⏳ الاشتراك ينتهي: *{}*",
    "farm": "🟢 تجميع", "all": "🔥 الكل", "followers": "🔵 متابعين", "likes": "🔴 لايكات", "views": "🟡 مشاهدات", "comments": "🟣 تعليقات",
    "accs": "📋 الحسابات", "add": "➕ إضافة", "stats": "📊 إحصائيات", "code": "🔑 تفعيل رمز",
    "back": "🔙 رجوع للقائمة الرئيسية", "start": "▶️ بدء", "stop": "🛑 إيقاف", "back_dev": "👑 عودة للوحة المطور",
    "join": "✅ تحقق من الاشتراك", "must_join": "🔐 اشترك في القنوات أولاً:",
    "expired": "⚠️ اشتراكك منتهي. أرسل رمز التفعيل:", "banned": "🚫 أنت محظور.",
    "code_ok": "✅ تم التفعيل بنجاح!", "code_bad": "❌ رمز خاطئ.",
    "price": "💰 *الأسعار الحالية*\n\n🔵 متابعين: 1.0\n🔴 لايكات: 1.0\n🟡 مشاهدات: 1.0\n🟣 تعليقات: 2.0",
    "dev": "👑 *لوحة تحكم المطور*\n\nيمكنك إدارة البوت بالكامل من هنا:",
    "gen": "🔑 توليد كود", "users": "👥 إدارة المستخدمين", "switch": "👤 الدخول كـ مستخدم",
    "add_ch": "➕ إضافة قناة", "del_ch": "🗑 حذف قناة", "update_code": "📤 تحديث الكود",
    "ask_code": "أرسل رمز التفعيل:", "ask_user": "أرسل يوزر تيك توك:", "ask_pass": "أرسل كلمة المرور:",
    "ask_ch_add": "أرسل معرف القناة (مثال: `@my_channel`):", "ch_added": "✅ تم إضافة القناة!", "ch_del": "✅ تم حذف القناة!",
    "ask_duration": "⏳ أرسل المدة (`5d` أيام، `10h` ساعات، `1m` أشهر):",
    "ask_uid": "أرسل آيدي (ID) المستخدم:", "mu_title": "⚙️ *إدارة المستخدم:* `{}`\n\n📋 الحسابات: *{}*\n🔢 الحد: *{}*\n⚡ السرعة: *{}*\n⏳ العمل: *{}*",
    "ask_limit": "أرسل رقم الحد الأقصى الجديد:", "ask_hours": "أرسل عدد ساعات العمل:",
    "ask_file": "📤 أرسل ملف `.py` الجديد الآن للتحديث وإعادة التشغيل:"
}

# ==========================================
# 🛡️ البروكسيات (خفيف)
# ==========================================
class ProxyPool:
    def __init__(self): self.proxies = []
    def acquire(self): return random.choice(self.proxies) if self.proxies else None
proxy_pool = ProxyPool()

def fetch_proxies_bg():
    try:
        r = requests.get("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt", timeout=10)
        lines = [l.strip() for l in r.text.splitlines() if l.strip()]
        for p in lines[:20]: proxy_pool.proxies.append(f"http://{p}")
    except: pass

# ==========================================
# 🌐 دوال الـ API
# ==========================================
def sign(ts, nonce, payload):
    return hmac.new(secretkey, f"{ts}-{nonce}-{payload}".encode(), hashlib.sha256).hexdigest()

def req(token, csrf, payload, op, auth=True, proxy=None):
    try:
        p_str = json.dumps(payload, separators=(',', ':'))
        ts, nonce = str(int(time.time()*1000)), str(uuid.uuid4())[:16]
        headers = {
            "X-APOLLO-OPERATION-NAME": op, "Content-Type": "application/json",
            "x-app-sig": sign(ts, nonce, p_str), "x-app-ts": ts, "x-app-nonce": nonce,
            "x-app-name": "com.dev.vidspark", "x-device-info": DEFAULT_DEVINFO,
            "User-Agent": "okhttp/4.12.0"
        }
        if auth: headers["token"], headers["x-csrf-token"] = token, csrf
        
        proxies = {"http": proxy, "https": proxy} if proxy else None
        r = requests.post(ENDPOINT, headers=headers, data=p_str, timeout=15, proxies=proxies)
        return r, r.json()
    except Exception as e:
        return None, {"error": str(e)}

async def farm_task(uid, uname, context):
    accs = USER_ACCOUNTS.get(str(uid), {})
    acc = accs.get(uname)
    if not acc: return
    start = time.time()
    
    while acc.get("farming"):
        user = get_user(uid)
        wh = user.get("work_hours", 16)
        sp = user.get("speed", "normal")
        
        if time.time() - start > (wh * 3600):
            acc["farming"] = False
            await context.bot.send_message(uid, f"⏳ الحساب {uname} أكمل {wh} ساعة. راحة.")
            await asyncio.sleep((24 - wh) * 3600)
            acc["farming"] = True
            start = time.time()
            
        try:
            payload = {"operationName": "GetOrders", "variables": {}, "query": "query GetOrders { getOrders { _id status } }"}
            _, res = await asyncio.to_thread(req, acc["token"], acc["csrf"], payload, "GetOrders", True, acc.get("proxy"))
            
            if res and "data" in res:
                pending = [o["_id"] for o in res["data"].get("getOrders", []) if o.get("status") == "pending"]
                for tid in pending:
                    if not acc.get("farming"): break
                    rn = random.randint(3000, 4500)
                    ap = {"operationName":"ActionOrder","variables":{"orderId":tid,"validationData":{"attempts":1,"initialNumber":float(rn),"timeSpent":4000,"actualCount":rn+1,"source":"CLIENT_CRONET"}},"query":"mutation ActionOrder($orderId: ID!, $validationData: ValidationDataInput!) { actionOrder(orderId: $orderId, validationData: $validationData) { score } }"}
                    _, ar = await asyncio.to_thread(req, acc["token"], acc["csrf"], ap, "ActionOrder", True, acc.get("proxy"))
                    
                    if ar and "data" in ar:
                        acc["score"] += int(ar["data"].get("actionOrder", {}).get("score", 0))
                        save_data()
                    
                    await asyncio.sleep(1 if sp=="fast" else 4 if sp=="slow" else 2)
            else:
                await asyncio.sleep(10)
        except asyncio.CancelledError: break
        except: await asyncio.sleep(5)

# ==========================================
# 🔘 الأزرار
# ==========================================
def get_main_kb(uid, is_owner=False):
    accs = USER_ACCOUNTS.get(str(uid), {})
    active = accs.get("_active", "None")
    score = accs.get(active, {}).get("score", 0)
    
    kb = [
        [InlineKeyboardButton(f"👤 {active} | ⭐ {score}", callback_data="accs")],
        [InlineKeyboardButton(T["farm"], callback_data="farm_menu"), InlineKeyboardButton(T["all"], callback_data="farm_all")],
        [InlineKeyboardButton(T["followers"], callback_data="prices"), InlineKeyboardButton(T["likes"], callback_data="prices")],
        [InlineKeyboardButton(T["views"], callback_data="prices"), InlineKeyboardButton(T["comments"], callback_data="prices")],
        [InlineKeyboardButton(T["accs"], callback_data="accs"), InlineKeyboardButton(T["add"], callback_data="add_acc")],
        [InlineKeyboardButton(T["stats"], callback_data="stats"), InlineKeyboardButton(T["code"], callback_data="enter_code")]
    ]
    if is_owner: kb.append([InlineKeyboardButton(T["back_dev"], callback_data="back_to_dev")])
    return InlineKeyboardMarkup(kb)

def get_dev_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(T["gen"], callback_data="dev_gen"), InlineKeyboardButton(T["users"], callback_data="dev_users")],
        [InlineKeyboardButton(T["add_ch"], callback_data="dev_add_ch"), InlineKeyboardButton(T["del_ch"], callback_data="dev_del_ch")],
        [InlineKeyboardButton(T["update_code"], callback_data="dev_update_code")],
        [InlineKeyboardButton(T["switch"], callback_data="switch_user")]
    ])

def get_back_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton(T["back"], callback_data="back")]])

def get_manage_user_kb(tid):
    u = get_user(tid)
    accs = USER_ACCOUNTS.get(str(tid), {})
    sp = {"fast": "🚀 سريع", "normal": "⚖️ عادي", "slow": "🐢 بطيء"}.get(u.get("speed", "normal"))
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📋 الحسابات ({len([k for k in accs if k != '_active'])})", callback_data=f"view_accs_{tid}")],
        [InlineKeyboardButton(f"🔢 الحد: {u.get('max_acc', 3)}", callback_data=f"set_lim_{tid}"), InlineKeyboardButton(f"⚡ السرعة: {sp}", callback_data=f"tog_sp_{tid}")],
        [InlineKeyboardButton(f"⏳ ساعات العمل: {u.get('work_hours', 16)}", callback_data=f"set_hr_{tid}")],
        [InlineKeyboardButton(T["back_dev"], callback_data="back_to_dev")]
    ])

# ==========================================
# 🚀 الأوامر
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = get_user(uid)
    is_user_mode = context.user_data.get("is_user_mode", False)
    
    if uid == OWNER_ID and not is_user_mode:
        return await update.effective_message.reply_text(T["dev"], reply_markup=get_dev_kb(), parse_mode=ParseMode.MARKDOWN)

    if user["blocked"]: return await update.effective_message.reply_text(T["banned"])
    if CHANNELS:
        kb = [[InlineKeyboardButton(f"📢 {ch}", url=f"https://t.me/{ch.replace('@','')}")] for ch in CHANNELS]
        kb.append([InlineKeyboardButton(T["join"], callback_data="check_join")])
        return await update.effective_message.reply_text(T["must_join"], reply_markup=InlineKeyboardMarkup(kb))

    if user["exp"] < time.time():
        user["starts"] += 1
        if user["starts"] > 5: user["blocked"] = True; save_data(); return await update.effective_message.reply_text(T["banned"])
        save_data()
        context.user_data["awaiting"] = "code"
        return await update.effective_message.reply_text(T["expired"])
    
    user["starts"] = 0; save_data()
    accs = USER_ACCOUNTS.setdefault(str(uid), {})
    active = accs.get("_active", "None")
    score = accs.get(active, {}).get("score", 0)
    days = round((user["exp"] - time.time()) / 86400, 1)
    
    text = T["menu"].format(active, score, len([k for k in accs if k != "_active"]), user.get("max_acc", 3), days)
    await update.effective_message.reply_text(text, reply_markup=get_main_kb(uid, uid==OWNER_ID), parse_mode=ParseMode.MARKDOWN)

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = update.effective_user.id
    data = q.data
    accs = USER_ACCOUNTS.setdefault(str(uid), {})
    user = get_user(uid)

    if data == "back":
        context.user_data.clear(); await start(update, context)
    elif data == "check_join":
        await start(update, context) 
    
    # ====== المطور ======
    elif data == "switch_user":
        context.user_data["is_user_mode"] = True
        if user["exp"] < time.time(): user["exp"] = time.time() + (365*86400)
        await start(update, context)
    elif data == "back_to_dev":
        context.user_data["is_user_mode"] = False; context.user_data.clear(); await start(update, context)
    elif data == "dev_update_code":
        context.user_data["awaiting"] = "update_code"
        await q.edit_message_text(T["ask_file"], reply_markup=get_back_kb(), parse_mode=ParseMode.MARKDOWN)
    elif data == "dev_gen":
        context.user_data["awaiting"] = "gen_duration"
        await q.edit_message_text(T["ask_duration"], reply_markup=get_back_kb(), parse_mode=ParseMode.MARKDOWN)
    elif data == "dev_add_ch":
        context.user_data["awaiting"] = "add_channel"
        await q.edit_message_text(T["ask_ch_add"], reply_markup=get_back_kb(), parse_mode=ParseMode.MARKDOWN)
    elif data == "dev_del_ch":
        if not CHANNELS: return await q.answer("لا توجد قنوات.", show_alert=True)
        kb = [[InlineKeyboardButton(f"❌ {ch}", callback_data=f"del_ch_{ch}")] for ch in CHANNELS]
        kb.append([InlineKeyboardButton(T["back"], callback_data="back_to_dev")])
        await q.edit_message_text("🗑 اختر القناة:", reply_markup=InlineKeyboardMarkup(kb))
    elif data.startswith("del_ch_"):
        ch = data.replace("del_ch_", "")
        if ch in CHANNELS: CHANNELS.remove(ch); save_data()
        await q.edit_message_text(T["ch_del"], reply_markup=get_back_kb(), parse_mode=ParseMode.MARKDOWN)
    elif data == "dev_users":
        context.user_data["awaiting"] = "manage_uid"
        await q.edit_message_text(T["ask_uid"], reply_markup=get_back_kb())
    elif data.startswith("view_accs_"):
        tid = data.split("_")[2]
        t_accs = USER_ACCOUNTS.get(str(tid), {})
        if not t_accs: return await q.answer("لا توجد حسابات.", show_alert=True)
        txt = f"📋 *حسابات المستخدم `{tid}`:*\n\n"
        for k, v in t_accs.items():
            if k != "_active": txt += f"👤 `{k}`: ⭐ {v.get('score', 0)} | {'✅ شغال' if v.get('farming') else '❌ متوقف'}\n"
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(T["back"], callback_data=f"back_manage_{tid}")]]), parse_mode=ParseMode.MARKDOWN)
    elif data.startswith("back_manage_"):
        tid = data.split("_")[2]
        u = get_user(tid)
        sp = {"fast": "🚀 سريع", "normal": "⚖️ عادي", "slow": "🐢 بطيء"}.get(u.get("speed", "normal"))
        text = T["mu_title"].format(tid, len([k for k in USER_ACCOUNTS.get(str(tid), {}) if k != '_active']), u.get("max_acc", 3), sp, u.get("work_hours", 16))
        await q.edit_message_text(text, reply_markup=get_manage_user_kb(tid), parse_mode=ParseMode.MARKDOWN)
    elif data.startswith("tog_sp_"):
        tid = data.split("_")[2]; u = get_user(tid)
        cur = u.get("speed", "normal")
        u["speed"] = "slow" if cur=="normal" else "fast" if cur=="slow" else "normal"
        save_data()
        sp = {"fast": "🚀 سريع", "normal": "⚖️ عادي", "slow": "🐢 بطيء"}[u["speed"]]
        await q.answer(f"تم التغيير إلى: {sp}", show_alert=True)
        await q.edit_message_text(T["mu_title"].format(tid, len([k for k in USER_ACCOUNTS.get(str(tid), {}) if k != '_active']), u.get("max_acc", 3), sp, u.get("work_hours", 16)), reply_markup=get_manage_user_kb(tid), parse_mode=ParseMode.MARKDOWN)
    elif data.startswith("set_lim_"):
        tid = data.split("_")[2]
        context.user_data.update({"awaiting": "mu_limit", "target_id": tid})
        await q.edit_message_text(T["ask_limit"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(T["back"], callback_data=f"back_manage_{tid}")]]))
    elif data.startswith("set_hr_"):
        tid = data.split("_")[2]
        context.user_data.update({"awaiting": "mu_hours", "target_id": tid})
        await q.edit_message_text(T["ask_hours"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(T["back"], callback_data=f"back_manage_{tid}")]]))

    # ====== المستخدم ======
    elif data == "prices": await q.edit_message_text(T["price"], reply_markup=get_back_kb(), parse_mode=ParseMode.MARKDOWN)
    elif data == "enter_code":
        context.user_data["awaiting"] = "code"
        await q.edit_message_text(T["ask_code"], reply_markup=get_back_kb())
    elif data == "add_acc":
        if len([k for k in accs if k != "_active"]) >= user.get("max_acc", 3):
            return await q.answer(f"الحد الأقصى {user.get('max_acc', 3)} حسابات!", show_alert=True)
        context.user_data["awaiting"] = "acc_user"
        await q.edit_message_text(T["ask_user"], reply_markup=get_back_kb())
    elif data == "accs":
        kb = [[InlineKeyboardButton(f"👤 {k} ⭐{v.get('score',0)}", callback_data=f"sw_{k}")] for k, v in accs.items() if k != "_active"]
        kb.append([InlineKeyboardButton(T["add"], callback_data="add_acc"), InlineKeyboardButton(T["back"], callback_data="back")])
        await q.edit_message_text(T["accs"], reply_markup=InlineKeyboardMarkup(kb))
    elif data.startswith("sw_"):
        accs["_active"] = data.split("_")[1]; await start(update, context)
    elif data == "farm_menu":
        active = accs.get("_active")
        if not active: return await q.answer("أضف حساباً أولاً!", show_alert=True)
        is_f = accs[active].get("farming", False)
        kb = [[InlineKeyboardButton(T["stop"] if is_f else T["start"], callback_data="stop_f" if is_f else "start_f")], [InlineKeyboardButton(T["back"], callback_data="back")]]
        await q.edit_message_text(f"حالة التجميع: `{active}`", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
    elif data == "start_f":
        active = accs.get("_active")
        if active and not accs[active].get("farming"):
            accs[active]["farming"] = True
            asyncio.create_task(farm_task(uid, active, context))
        await start(update, context)
    elif data == "stop_f":
        active = accs.get("_active")
        if active: accs[active]["farming"] = False
        await start(update, context)
    elif data == "stats":
        total = sum(v.get("score",0) for k,v in accs.items() if k != "_active")
        txt = f"📊 *إحصائياتك*\n\n💰 المجموع: *{total}*\n\n"
        for k, v in accs.items():
            if k != "_active": txt += f"👤 `{k}`: ⭐ {v.get('score',0)}\n"
        await q.edit_message_text(txt, reply_markup=get_back_kb(), parse_mode=ParseMode.MARKDOWN)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    aw = context.user_data.get("awaiting")
    accs = USER_ACCOUNTS.setdefault(str(uid), {})

    # إدخالات المطور
    if aw == "manage_uid" and uid == OWNER_ID:
        if text not in USERS: return await update.message.reply_text("❌ غير موجود.")
        u = get_user(text)
        sp = {"fast": "🚀 سريع", "normal": "⚖️ عادي", "slow": "🐢 بطيء"}.get(u.get("speed", "normal"))
        context.user_data.clear()
        await update.message.reply_text(T["mu_title"].format(text, len([k for k in USER_ACCOUNTS.get(text, {}) if k != '_active']), u.get("max_acc", 3), sp, u.get("work_hours", 16)), reply_markup=get_manage_user_kb(text), parse_mode=ParseMode.MARKDOWN)
    elif aw == "mu_limit" and uid == OWNER_ID:
        try:
            tid = context.user_data.get("target_id")
            get_user(tid)["max_acc"] = int(text); save_data(); context.user_data.clear()
            await update.message.reply_text(f"✅ تم التعديل إلى {text}.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(T["back"], callback_data=f"back_manage_{tid}")]]))
        except: await update.message.reply_text("❌ رقم خاطئ.")
    elif aw == "mu_hours" and uid == OWNER_ID:
        try:
            tid = context.user_data.get("target_id")
            h = int(text)
            if not (1 <= h <= 24): raise ValueError
            get_user(tid)["work_hours"] = h; save_data(); context.user_data.clear()
            await update.message.reply_text(f"✅ تم تعديل الساعات إلى {h}.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(T["back"], callback_data=f"back_manage_{tid}")]]))
        except: await update.message.reply_text("❌ رقم من 1 إلى 24.")
    elif aw == "gen_duration" and uid == OWNER_ID:
        text = text.lower()
        secs = float(text[:-1]) * (3600 if text.endswith("h") else 86400 if text.endswith("d") else 30*86400) if text[-1] in "hdm" else float(text)*86400
        c = str(uuid.uuid4())[:6].upper()
        CODES[c] = {"seconds": secs, "used": False}; save_data(); context.user_data.clear()
        await update.message.reply_text(f"✅ الكود: `{c}`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_back_kb())
    elif aw == "add_channel" and uid == OWNER_ID:
        ch = text if text.startswith("@") or text.startswith("-") else "@" + text
        if ch not in CHANNELS: CHANNELS.append(ch); save_data()
        context.user_data.clear(); await update.message.reply_text(T["ch_added"], reply_markup=get_back_kb())
    
    # إدخالات المستخدم
    elif aw == "code":
        if text in CODES and not CODES[text]["used"]:
            CODES[text]["used"] = True
            get_user(uid)["exp"] = max(time.time(), get_user(uid).get("exp", 0)) + CODES[text]["seconds"]; save_data()
            await update.message.reply_text(T["code_ok"]); await start(update, context)
        else: await update.message.reply_text(T["code_bad"])
        context.user_data.clear()
    elif aw == "acc_user":
        context.user_data["temp_u"] = text; context.user_data["awaiting"] = "acc_pass"
        await update.message.reply_text(T["ask_pass"])
    elif aw == "acc_pass":
        uname, pwd = context.user_data.pop("temp_u"), text
        context.user_data.clear()
        msg = await update.message.reply_text("⏳ جاري التحقق...")
        
        # 1. AttestDevice (تجاوز الحماية)
        attest = {"operationName": "AttestDevice", "variables": {"integrityToken": "CpsCARCnMGtvLkiuhYFGDW3rUoE73im9X9NmXA1cHOZZOzgRp5FtsmIrZBoNek0K7XIoZiR9XKg1bpApXNem9MbcR4UiIxz1n4Wgv_LA4hSSAbHzpaAfXcnLyKgwnOXGRUieQ4OOpMTMDRxD6O7kd3jjAfcbcHFt3bdgyw7CJYpxz4oq3lIti658lCdnt1NvJzUwfYSp6eWKcvKV5lScaq-nkplRn7hz38A8kLhYNx6w-7rne41hWCR6BQISVfBewaqeh7RL-9iEDrzK-ECbdEwBnpO_LfAqCJKn1bf5VkVxuPAz5qPvB8cNE7ZBMAyMnDHdjNDwpnZMA2EXsgRsyT6Fm_l3MNugWDdWbRgww6sAw6KrRzeBDETsXTh1ZBpqAWerZWp6AIjaDa-b0NFbOS69HsGnfpE7hljmu3OTsd4tM6nM50qiSc4QGuD4aM-joJFJYKIsWf_grquB66tYnYa2mCWcPl1hIEApHMXbCLiO7nwX-8LXEwCDvVNT4f8mjgtI1__D_C_f4g", "requestHash": "gPyB7FF-XeZc2kwi2L-KZXs21Z8oPErvHD9gn572PyR"}, "query": "mutation AttestDevice($integrityToken: String!, $requestHash: String!) { attestDevice(integrityToken: $integrityToken, requestHash: $requestHash) { ok verified } }"}
        await asyncio.to_thread(req, "", "", attest, "AttestDevice", False)
        
        # 2. تسجيل الدخول
        payload = {"operationName": "LoginAccount", "variables": {"data": {"uniqueId": uname, "password": pwd, "authMethod": "local"}}, "query": "mutation LoginAccount($data: TiktokInfo) { loginTiktok(data: $data) { accessToken user { score } } }"}
        r, res = await asyncio.to_thread(req, "", "", payload, "LoginAccount", False)
        
        if r and res and "data" in res and res["data"].get("loginTiktok"):
            accs[uname] = {"token": res["data"]["loginTiktok"]["accessToken"], "csrf": r.headers.get("x-csrf-token", DEFAULT_CSRF), "score": res["data"]["loginTiktok"]["user"].get("score",0), "farming": False, "password": pwd, "proxy": proxy_pool.acquire()}
            accs["_active"] = uname; save_data()
            await msg.edit_text("✅ تم الإضافة!"); await start(update, context)
        else:
            err = res['errors'][0].get('message', 'بيانات خاطئة') if res and "errors" in res else res.get("error", "فشل الاتصال")
            await msg.edit_text(f"❌ خطأ من السيرفر: {err}")

async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != OWNER_ID or context.user_data.get("awaiting") != "update_code": return
    
    doc = update.message.document
    if not doc.file_name.endswith(".py"): return await update.message.reply_text("❌ يجب أن يكون الملف `.py`")
        
    msg = await update.message.reply_text("⏳ جاري التحديث...")
    try:
        file = await context.bot.get_file(doc.file_id)
        script = os.path.abspath(__file__)
        if os.path.exists(script): os.remove(script)
        await file.download_to_drive(script)
        await msg.edit_text("✅ تم التحديث!\n🔄 جاري إعادة التشغيل...")
        await asyncio.sleep(2)
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {e}")

def main():
    load_data()
    threading.Thread(target=fetch_proxies_bg, daemon=True).start()
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    
    print("✅ Lite Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    import threading
    main()
