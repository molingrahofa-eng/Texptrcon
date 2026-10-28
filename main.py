#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikSpark Telegram Bot — The Absolute Ultimate Edition
Contains: Proxies, Matplotlib Stats, Auto-Relogin, 16/8 Farming, Limits, Subscriptions, Auto-Update via .py file.
"""

import os
import sys
import json
import time
import random
import asyncio
import hashlib
import hmac
import uuid
import io
import signal
import traceback
import threading
import concurrent.futures
from datetime import datetime, timezone, timedelta
import requests

# محاولة استيراد مكتبات الرسم البياني والتشفير
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.constants import ParseMode

# ==========================================
# 🎨 كود ألوان الكونسول (المطور: kilj)
# ==========================================
IS_TERMINAL = sys.stdout.isatty()
def c(text, color_code):
    if IS_TERMINAL: return f"{color_code}{text}\033[0m"
    return text

res = '\033[0m'; E1 = '\033[1m'; r = '\033[31m'; g = '\033[32m'; y = '\033[33m'; G = '\033[92m'; Y = '\033[93m'; B = '\033[94m'

# ==========================================
# ⚙️ الإعدادات الأساسية
# ==========================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "6198804155:AAF5Zj-co6guQ6s2bW5hMTvFga8CFRi0WqA")
try:
    OWNER_ID = int(os.environ.get("OWNER_ID", "5952132218"))
except:
    OWNER_ID = 5952132218

DEFAULT_DEVINFO = '{"d":"61393235613366373261636533656632","n":"494e46494e495820496e66696e6978204c697465203330","o":"16","t":"d","v":"2.2.9","s":"0,0"}'
USER_AGENTS = ["okhttp/4.12.0", "okhttp/4.11.0", "okhttp/4.10.0"]
keybytes = [0x35, 0x30, 0x1c, 0x2f, 0x2c, 0x2c, 0x28, 0x31, 0x35, 0x30, 0x1c, 0x2f, 0x2c, 0x2c, 0x28, 0x31]
secretkey = bytes([b ^ 0x43 for b in keybytes])

OPERATION_IDS = {
    "LoginAccount": "3522613813036d73817b2715e67743f8d23d7a85ad08b7e12aa3b29a24a17c43",
    "AttestDevice": "bfaf5a72aeb9a337811da6a6d13e0b73680a18ffde0c59a23701e55b98ac2515",
    "GetOrders": "330a1eb97775a2f520b2e848601c40f8211d171c778c18840b37260ce94fb725",
    "ActionOrder": "5177239275a5e78347f7d925501b1a774b76a086f67c33b0033c740dd676f62b",
    "CreateOrder": "ad7a6397c3970b1e7601f69d24989bff330e256ee5e39321a8d1ad3fe3879b48",
}
ENDPOINT = "https://api.tikspark.xyz/graphql"
DEFAULT_CSRF = "1786692648457:b5fb61a1a92b2de8ffa0343c5d45ce9f1e578abb695cca7ab6659cfc29f85fe9"
BAN_CODES = {403, 407, 429}
AUTH_FATAL = ("unauthorized", "token expired", "invalid token", "not authenticated", "jwt")

DATA_FILE = "data.json"
DYNAMIC_PRICES = {"followers": 1.0, "likes": 1.0, "views": 1.0, "comments": 2.0}

FREE_PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
]

# ==========================================
# 💾 قاعدة البيانات والحفظ (JSON)
# ==========================================
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
        except Exception as e:
            print(c(f"[Storage] Load error: {e}", r))

def get_user(uid):
    uid = str(uid)
    if uid not in USERS:
        USERS[uid] = {"exp": 0, "lang": "ar", "max_acc": 3, "blocked": False, "starts": 0, "speed": "normal", "work_hours": 16}
    return USERS[uid]

# ==========================================
# 🌐 الترجمات
# ==========================================
TEXTS = {
    "ar": {
        "menu": "🏠 *القائمة الرئيسية*\n\n👤 النشط: `{}` | ⭐ *{}*\n📋 الحسابات: *{}* من أصل *{}*\n⏳ الاشتراك ينتهي: *{}*",
        "farm": "🟢 تجميع", "all": "🔥 الكل", "followers": "🔵 متابعين", "likes": "🔴 لايكات", "views": "🟡 مشاهدات", "comments": "🟣 تعليقات",
        "accs": "📋 الحسابات", "add": "➕ إضافة", "stats": "📊 إحصائيات", "lang": "🌐 اللغة", "code": "🔑 تفعيل رمز",
        "back": "🔙 رجوع للقائمة الرئيسية", "start": "▶️ بدء", "stop": "🛑 إيقاف", "back_dev": "👑 عودة للوحة المطور",
        "join": "✅ تحقق من الاشتراك", "must_join": "🔐 اشترك في القنوات أولاً:",
        "expired": "⚠️ اشتراكك منتهي. أرسل رمز التفعيل:", "banned": "🚫 أنت محظور.",
        "code_ok": "✅ تم التفعيل بنجاح!", "code_bad": "❌ رمز خاطئ.",
        "price": "💰 *الأسعار الحالية*\n\n🔵 متابعين: {} نقطة\n🔴 لايكات: {} نقطة\n🟡 مشاهدات: {} نقطة\n🟣 تعليقات: {} نقطة\n\nأرسل الكمية والرابط في رسالة واحدة.",
        "dev": "👑 *لوحة تحكم المطور*\n\nيمكنك إدارة البوت بالكامل من هنا:",
        "gen": "🔑 توليد كود", "users": "👥 إدارة المستخدمين", "switch": "👤 الدخول كـ مستخدم",
        "add_ch": "➕ إضافة قناة", "del_ch": "🗑 حذف قناة", "update_code": "📤 تحديث الكود",
        "ask_code": "أرسل رمز التفعيل الآن:", "ask_user": "أرسل يوزر تيك توك:", "ask_pass": "أرسل كلمة المرور:",
        "ask_ch_add": "أرسل معرف القناة (مثال: `@my_channel`):",
        "ask_duration": "⏳ أرسل مدة الاشتراك:\n\n📌 *للأيام:* `5d`\n📌 *للساعات:* `10h`\n📌 *للأشهر:* `1m`\n\n(إذا أرسلت رقماً فقط، سيتم اعتباره أياماً)",
        "ch_added": "✅ تم إضافة القناة بنجاح!", "ch_del": "✅ تم حذف القناة!", "no_ch": "لا توجد قنوات لحذفها.",
        "ask_uid": "أرسل آيدي (ID) المستخدم الذي تريد إدارته:",
        "mu_title": "⚙️ *إدارة المستخدم:* `{}`\n\n📋 عدد الحسابات: *{}*\n🔢 الحد الأقصى: *{}*\n⚡ السرعة: *{}*\n⏳ ساعات العمل: *{}*",
        "ask_limit": "أرسل الرقم الجديد للحد الأقصى للحسابات (مثال: 5):",
        "ask_hours": "أرسل عدد ساعات العمل (مثال: 12 أو 16):",
        "speed_changed": "✅ تم تغيير سرعة المستخدم إلى: *{}*",
        "limit_changed": "✅ تم تغيير الحد الأقصى إلى: *{}*",
        "hours_changed": "✅ تم تغيير ساعات العمل إلى: *{}* ساعة",
        "user_not_found": "❌ هذا المستخدم غير موجود في قاعدة البيانات.",
        "ask_file": "📤 أرسل ملف البايثون (`.py`) الجديد الآن، وسأقوم باستبدال الكود وإعادة التشغيل فوراً:",
        "updating": "⏳ جاري استلام الملف واستبداله...",
        "bad_file": "❌ خطأ: يجب أن يكون الملف بصيغة `.py` فقط."
    },
    "en": {
        "menu": "🏠 *Main Menu*\n\n👤 Active: `{}` | ⭐ *{}*\n📋 Accounts: *{} / {}*\n⏳ Sub: *{}*",
        "farm": "🟢 Farm", "all": "🔥 All", "followers": "🔵 Followers", "likes": "🔴 Likes", "views": "🟡 Views", "comments": "🟣 Comments",
        "accs": "📋 Accounts", "add": "➕ Add", "stats": "📊 Stats", "lang": "🌐 Language", "code": "🔑 Enter Code",
        "back": "🔙 Back to Main Menu", "start": "▶️ Start", "stop": "🛑 Stop", "back_dev": "👑 Back to Dev Panel",
        "join": "✅ Check Join", "must_join": "🔐 Join channels first:",
        "expired": "⚠️ Subscription expired. Send code:", "banned": "🚫 You are banned.",
        "code_ok": "✅ Activated successfully!", "code_bad": "❌ Invalid code.",
        "price": "💰 *Prices*\n\n🔵 Followers: {}\n🔴 Likes: {}\n🟡 Views: {}\n🟣 Comments: {}\n\nSend amount and link in one message.",
        "dev": "👑 *Dev Panel*",
        "gen": "🔑 Gen Code", "users": "👥 Users", "switch": "👤 Switch to User",
        "add_ch": "➕ Add Channel", "del_ch": "🗑 Delete Channel", "update_code": "📤 Update Code",
        "ask_code": "Send code:", "ask_user": "Send TikTok Username:", "ask_pass": "Send Password:",
        "ask_ch_add": "Send channel ID (e.g., `@my_channel`):",
        "ask_duration": "⏳ Send duration:\n\n📌 *Days:* `5d`\n📌 *Hours:* `10h`\n📌 *Months:* `1m`",
        "ch_added": "✅ Channel added!", "ch_del": "✅ Channel deleted!", "no_ch": "No channels to delete.",
        "ask_uid": "Send user ID to manage:",
        "mu_title": "⚙️ *Manage User:* `{}`\n\n📋 Accounts: *{}*\n🔢 Max Limit: *{}*\n⚡ Speed: *{}*\n⏳ Work Hours: *{}*",
        "ask_limit": "Send new max accounts limit (e.g., 5):",
        "ask_hours": "Send work hours (e.g., 12 or 16):",
        "speed_changed": "✅ Speed changed to: *{}*",
        "limit_changed": "✅ Max limit changed to: *{}*",
        "hours_changed": "✅ Work hours changed to: *{}* hours",
        "user_not_found": "❌ User not found in database.",
        "ask_file": "📤 Send the new Python file (`.py`) now to replace code and restart:",
        "updating": "⏳ Receiving file and replacing...",
        "bad_file": "❌ Error: File must be `.py`."
    }
}

def t(uid, key):
    lang = get_user(uid).get("lang", "ar")
    return TEXTS.get(lang, TEXTS["ar"]).get(key, key)

# ==========================================
# 🛡️ نظام البروكسيات (Proxy Pool)
# ==========================================
class ProxyEndpoint:
    def __init__(self, url):
        self.url = url
        self.failures = 0
        self.banned_until = None
    def is_available(self):
        return not (self.banned_until and datetime.now(timezone.utc) < self.banned_until)
    def mark_failed(self):
        self.failures += 1
        self.banned_until = datetime.now(timezone.utc) + timedelta(seconds=min(60 * (2 ** max(self.failures-1, 0)), 3600))
    def mark_ok(self):
        self.failures = 0
        self.banned_until = None

class ProxyPool:
    def __init__(self):
        self.proxies = []
        self._lock = threading.Lock()
    def acquire(self):
        with self._lock:
            avail = [p for p in self.proxies if p.is_available()]
        return random.choice(avail) if avail else None
    def add(self, url):
        with self._lock:
            if not any(p.url == url for p in self.proxies):
                self.proxies.append(ProxyEndpoint(url))

proxy_pool = ProxyPool()

def _download_raw():
    raw = set()
    def fetch(url):
        try:
            r = requests.get(url, timeout=10)
            return [l.strip() for l in r.text.splitlines() if l.strip() and not l.startswith("#")]
        except: return []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        for lines in ex.map(fetch, FREE_PROXY_SOURCES): raw.update(lines)
    return raw

def _validate_proxy(proxy_url):
    try:
        s = requests.Session(); s.trust_env = False
        s.proxies = {"http": proxy_url, "https": proxy_url}
        r = s.get("https://api.ipify.org", timeout=5)
        return r.status_code == 200
    except: return False

def fetch_free_proxies():
    raw = _download_raw()
    normalized = ["http://" + p if "://" not in p else p for p in raw]
    fresh = [p for p in normalized if not any(px.url == p for px in proxy_pool.proxies)][:50]
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        for url, ok in zip(fresh, ex.map(_validate_proxy, fresh)):
            if ok: proxy_pool.add(url)
    print(c(f"[Proxy] ✅ Updated proxies. Available: {len(proxy_pool.proxies)}", G))

# ==========================================
# 🌐 دوال الـ API
# ==========================================
def sign(ts, nonce, payload):
    return hmac.new(secretkey, f"{ts}-{nonce}-{payload}".encode(), hashlib.sha256).hexdigest()

def req(token, csrf, payload, op, auth=True, proxy_url=None):
    try:
        p_str = json.dumps(payload, separators=(',', ':'))
        ts, nonce = str(int(time.time()*1000)), str(uuid.uuid4())[:16]
        headers = {
            "X-APOLLO-OPERATION-NAME": op, "Content-Type": "application/json",
            "x-app-sig": sign(ts, nonce, p_str), "x-app-ts": ts, "x-app-nonce": nonce,
            "x-app-name": "com.dev.vidspark", "x-device-info": DEFAULT_DEVINFO,
            "User-Agent": random.choice(USER_AGENTS), "Accept-Encoding": "gzip"
        }
        if auth: headers["token"], headers["x-csrf-token"] = token, csrf
        
        s = requests.Session(); s.trust_env = False
        if proxy_url: s.proxies = {"http": proxy_url, "https": proxy_url}
        
        r = s.post(ENDPOINT, headers=headers, data=p_str, timeout=(10, 20))
        r.raise_for_status()
        return r, r.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in BAN_CODES: return None, {"__banned__": True}
        return None, {"error": str(e)}
    except Exception as e:
        return None, {"error": str(e)}

def req_with_retry(token, csrf, payload, op, auth, acc):
    for attempt in range(3):
        proxy = acc.get("proxy") if acc else None
        pu = proxy.url if proxy else None
        resp, res = req(token, csrf, payload, op, auth, pu)
        
        if res and "error" not in res and "__banned__" not in res:
            if proxy: proxy.mark_ok()
            return resp, res
            
        if proxy: proxy.mark_failed()
        if acc: acc["proxy"] = proxy_pool.acquire()
        time.sleep(2)
    return None, {"error": "Failed after retries"}

async def try_relogin(uid, uname):
    acc = USER_ACCOUNTS.get(str(uid), {}).get(uname)
    if not acc or not acc.get("password"): return False
    payload = {"operationName": "LoginAccount", "variables": {"data": {"uniqueId": uname, "password": acc["password"], "authMethod": "local"}}, "query": "mutation LoginAccount($data: TiktokInfo) { loginTiktok(data: $data) { accessToken user { score } } }"}
    resp, res = await asyncio.to_thread(req, "", "", payload, "LoginAccount", False)
    if resp and res and "data" in res:
        acc["token"] = res["data"]["loginTiktok"]["accessToken"]
        acc["csrf"] = resp.headers.get("x-csrf-token") or DEFAULT_CSRF
        acc["_needs_relogin"] = False
        save_data()
        return True
    return False

async def fetch_prices():
    global DYNAMIC_PRICES
    query = "query GetServices { getServices { type price } }"
    try:
        resp = await asyncio.to_thread(requests.post, ENDPOINT, json={"query": query}, timeout=10)
        if resp.status_code == 200:
            for srv in resp.json().get("data", {}).get("getServices", []):
                DYNAMIC_PRICES[srv.get("type").lower()] = float(srv.get("price", 1.0))
    except: pass

# ==========================================
# 🚜 دالة التجميع (تقرأ السرعة والساعات)
# ==========================================
async def farm_task(uid, uname, context):
    accs = USER_ACCOUNTS.get(str(uid), {})
    acc = accs.get(uname)
    if not acc: return
    start = time.time()
    
    while acc.get("farming"):
        user = get_user(uid)
        work_hours = user.get("work_hours", 16)
        speed = user.get("speed", "normal")
        work_seconds = work_hours * 3600
        
        if time.time() - start > work_seconds:
            acc["farming"] = False
            rest_hours = 24 - work_hours
            try: await context.bot.send_message(uid, f"⏳ الحساب {uname} أكمل {work_hours} ساعة. راحة {rest_hours} ساعة.")
            except: pass
            await asyncio.sleep(rest_hours * 3600)
            acc["farming"] = True
            start = time.time()

        if acc.get("_needs_relogin"):
            if not await try_relogin(uid, uname):
                await asyncio.sleep(60); continue
            
        try:
            payload = {"operationName": "GetOrders", "variables": {}, "query": "query GetOrders { getOrders { _id status } }"}
            _, res = await asyncio.to_thread(req_with_retry, acc["token"], acc["csrf"], payload, "GetOrders", True, acc)
            
            if res and "data" in res:
                pending = [o["_id"] for o in res["data"].get("getOrders", []) if o.get("status") == "pending"]
                for tid in pending:
                    if not acc.get("farming"): break
                    rn = random.randint(3000, 4500)
                    ap = {"operationName":"ActionOrder","variables":{"orderId":tid,"validationData":{"attempts":1,"initialNumber":float(rn),"timeSpent":4000,"actualCount":rn+1,"source":"CLIENT_CRONET"}},"query":"mutation ActionOrder($orderId: ID!, $validationData: ValidationDataInput!) { actionOrder(orderId: $orderId, validationData: $validationData) { score } }"}
                    _, ar = await asyncio.to_thread(req_with_retry, acc["token"], acc["csrf"], ap, "ActionOrder", True, acc)
                    if ar and "data" in ar:
                        acc["score"] += int(ar["data"].get("actionOrder", {}).get("score", 0))
                        save_data()
                    
                    if speed == "fast": await asyncio.sleep(1)
                    elif speed == "slow": await asyncio.sleep(4)
                    else: await asyncio.sleep(2)
            else:
                await asyncio.sleep(10)
        except asyncio.CancelledError: break
        except: await asyncio.sleep(5)

# ==========================================
# 🔘 تصميم الأزرار
# ==========================================
def get_main_kb(uid, is_owner=False):
    accs = USER_ACCOUNTS.get(str(uid), {})
    active = accs.get("_active", "None")
    score = accs.get(active, {}).get("score", 0)
    
    kb = [
        [InlineKeyboardButton(f"👤 {active} | ⭐ {score}", callback_data="accs")],
        [InlineKeyboardButton(t(uid, "farm"), callback_data="farm_menu"), InlineKeyboardButton(t(uid, "all"), callback_data="farm_all")],
        [InlineKeyboardButton(t(uid, "followers"), callback_data="prices"), InlineKeyboardButton(t(uid, "likes"), callback_data="prices")],
        [InlineKeyboardButton(t(uid, "views"), callback_data="prices"), InlineKeyboardButton(t(uid, "comments"), callback_data="prices")],
        [InlineKeyboardButton(t(uid, "accs"), callback_data="accs"), InlineKeyboardButton(t(uid, "add"), callback_data="add_acc")],
        [InlineKeyboardButton(t(uid, "stats"), callback_data="stats"), InlineKeyboardButton(t(uid, "lang"), callback_data="lang_menu")],
        [InlineKeyboardButton(t(uid, "code"), callback_data="enter_code")]
    ]
    if is_owner: kb.append([InlineKeyboardButton(t(uid, "back_dev"), callback_data="back_to_dev")])
    return InlineKeyboardMarkup(kb)

def get_dev_kb(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(uid, "gen"), callback_data="dev_gen"), InlineKeyboardButton(t(uid, "users"), callback_data="dev_users")],
        [InlineKeyboardButton(t(uid, "add_ch"), callback_data="dev_add_ch"), InlineKeyboardButton(t(uid, "del_ch"), callback_data="dev_del_ch")],
        [InlineKeyboardButton(t(uid, "update_code"), callback_data="dev_update_code")],
        [InlineKeyboardButton(t(uid, "switch"), callback_data="switch_user")]
    ])

def get_back_kb(uid):
    return InlineKeyboardMarkup([[InlineKeyboardButton(t(uid, "back"), callback_data="back")]])

def get_manage_user_kb(target_id):
    user = get_user(target_id)
    accs = USER_ACCOUNTS.get(str(target_id), {})
    speed_val = user.get("speed", "normal")
    speed_txt = {"fast": "🚀 سريع", "normal": "⚖️ عادي", "slow": "🐢 بطيء"}.get(speed_val, speed_val)
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📋 حسابات المستخدم ({len([k for k in accs if k != '_active'])})", callback_data=f"view_accs_{target_id}")],
        [InlineKeyboardButton(f"🔢 الحد الأقصى: {user.get('max_acc', 3)}", callback_data=f"set_lim_{target_id}")],
        [InlineKeyboardButton(f"⚡ السرعة: {speed_txt}", callback_data=f"toggle_speed_{target_id}")],
        [InlineKeyboardButton(f"⏳ ساعات العمل: {user.get('work_hours', 16)}", callback_data=f"set_hours_{target_id}")],
        [InlineKeyboardButton(t(OWNER_ID, "back"), callback_data="back_to_dev")]
    ])

# ==========================================
# 🚀 الأوامر الأساسية
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = get_user(uid)
    is_user_mode = context.user_data.get("is_user_mode", False)
    
    asyncio.create_task(fetch_prices())

    if uid == OWNER_ID and not is_user_mode:
        return await update.effective_message.reply_text(t(uid, "dev"), reply_markup=get_dev_kb(uid), parse_mode=ParseMode.MARKDOWN)

    if user["blocked"]: return await update.effective_message.reply_text(t(uid, "banned"))
    if CHANNELS:
        kb = [[InlineKeyboardButton(f"📢 {ch}", url=f"https://t.me/{ch.replace('@','')}")] for ch in CHANNELS]
        kb.append([InlineKeyboardButton(t(uid, "join"), callback_data="check_join")])
        return await update.effective_message.reply_text(t(uid, "must_join"), reply_markup=InlineKeyboardMarkup(kb))

    if user["exp"] < time.time():
        user["starts"] += 1
        if user["starts"] > 5: user["blocked"] = True; save_data(); return await update.effective_message.reply_text(t(uid, "banned"))
        save_data()
        context.user_data["awaiting"] = "code"
        return await update.effective_message.reply_text(t(uid, "expired"))
    
    user["starts"] = 0
    save_data()
    
    accs = USER_ACCOUNTS.setdefault(str(uid), {})
    active = accs.get("_active", "None")
    score = accs.get(active, {}).get("score", 0)
    days = round((user["exp"] - time.time()) / 86400, 1)
    
    text = t(uid, "menu").format(active, score, len([k for k in accs if k != "_active"]), user.get("max_acc", 3), days)
    await update.effective_message.reply_text(text, reply_markup=get_main_kb(uid, is_owner=(uid==OWNER_ID)), parse_mode=ParseMode.MARKDOWN)

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = update.effective_user.id
    data = q.data
    accs = USER_ACCOUNTS.setdefault(str(uid), {})
    user = get_user(uid)

    if data == "back":
        context.user_data.clear()
        await start(update, context)
    elif data == "check_join":
        await start(update, context) 
    
    # ================= قوائم المطور =================
    elif data == "switch_user":
        context.user_data["is_user_mode"] = True
        if user["exp"] < time.time(): user["exp"] = time.time() + (365*86400)
        await start(update, context)
    elif data == "back_to_dev":
        context.user_data["is_user_mode"] = False
        context.user_data.clear()
        await start(update, context)
        
    elif data == "dev_update_code":
        context.user_data["awaiting"] = "update_code"
        await q.edit_message_text(t(uid, "ask_file"), reply_markup=get_back_kb(uid), parse_mode=ParseMode.MARKDOWN)
        
    elif data == "dev_gen":
        context.user_data["awaiting"] = "gen_duration"
        await q.edit_message_text(t(uid, "ask_duration"), reply_markup=get_back_kb(uid), parse_mode=ParseMode.MARKDOWN)
        
    elif data == "dev_add_ch":
        context.user_data["awaiting"] = "add_channel"
        await q.edit_message_text(t(uid, "ask_ch_add"), reply_markup=get_back_kb(uid), parse_mode=ParseMode.MARKDOWN)
        
    elif data == "dev_del_ch":
        if not CHANNELS: return await q.answer(t(uid, "no_ch"), show_alert=True)
        kb = [[InlineKeyboardButton(f"❌ {ch}", callback_data=f"del_ch_{ch}")] for ch in CHANNELS]
        kb.append([InlineKeyboardButton(t(uid, "back"), callback_data="back_to_dev")])
        await q.edit_message_text("🗑 اختر القناة لحذفها:", reply_markup=InlineKeyboardMarkup(kb))
        
    elif data.startswith("del_ch_"):
        ch = data.replace("del_ch_", "")
        if ch in CHANNELS: CHANNELS.remove(ch); save_data()
        await q.edit_message_text(t(uid, "ch_del"), reply_markup=get_back_kb(uid), parse_mode=ParseMode.MARKDOWN)

    elif data == "dev_users":
        context.user_data["awaiting"] = "manage_uid"
        await q.edit_message_text(t(uid, "ask_uid"), reply_markup=get_back_kb(uid))
        
    elif data.startswith("view_accs_"):
        target_id = data.split("_")[2]
        target_accs = USER_ACCOUNTS.get(str(target_id), {})
        if not target_accs: return await q.answer("لا توجد حسابات لهذا المستخدم.", show_alert=True)
            
        txt = f"📋 *حسابات المستخدم `{target_id}`:*\n\n"
        for k, v in target_accs.items():
            if k != "_active":
                txt += f"👤 `{k}`: ⭐ {v.get('score', 0)} | {'✅ شغال' if v.get('farming') else '❌ متوقف'}\n"
        kb = [[InlineKeyboardButton(t(uid, "back"), callback_data=f"back_manage_{target_id}")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
        
    elif data.startswith("back_manage_"):
        target_id = data.split("_")[2]
        target_user = get_user(target_id)
        speed_txt = {"fast": "🚀 سريع", "normal": "⚖️ عادي", "slow": "🐢 بطيء"}.get(target_user.get("speed", "normal"))
        text = t(uid, "mu_title").format(target_id, len([k for k in USER_ACCOUNTS.get(str(target_id), {}) if k != '_active']), target_user.get("max_acc", 3), speed_txt, target_user.get("work_hours", 16))
        await q.edit_message_text(text, reply_markup=get_manage_user_kb(target_id), parse_mode=ParseMode.MARKDOWN)

    elif data.startswith("toggle_speed_"):
        target_id = data.split("_")[2]
        target_user = get_user(target_id)
        current = target_user.get("speed", "normal")
        new_speed = "slow" if current == "normal" else "fast" if current == "slow" else "normal"
        target_user["speed"] = new_speed
        save_data()
        speed_txt = {"fast": "🚀 سريع", "normal": "⚖️ عادي", "slow": "🐢 بطيء"}.get(new_speed)
        await q.answer(t(uid, "speed_changed").format(speed_txt), show_alert=True)
        text = t(uid, "mu_title").format(target_id, len([k for k in USER_ACCOUNTS.get(str(target_id), {}) if k != '_active']), target_user.get("max_acc", 3), speed_txt, target_user.get("work_hours", 16))
        await q.edit_message_text(text, reply_markup=get_manage_user_kb(target_id), parse_mode=ParseMode.MARKDOWN)

    elif data.startswith("set_lim_"):
        target_id = data.split("_")[2]
        context.user_data["awaiting"] = "mu_limit"
        context.user_data["target_id"] = target_id
        await q.edit_message_text(t(uid, "ask_limit"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(uid, "back"), callback_data=f"back_manage_{target_id}")]]))

    elif data.startswith("set_hours_"):
        target_id = data.split("_")[2]
        context.user_data["awaiting"] = "mu_hours"
        context.user_data["target_id"] = target_id
        await q.edit_message_text(t(uid, "ask_hours"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(uid, "back"), callback_data=f"back_manage_{target_id}")]]))

    # ================= قوائم المستخدم =================
    elif data == "prices":
        txt = t(uid, "price").format(DYNAMIC_PRICES["followers"], DYNAMIC_PRICES["likes"], DYNAMIC_PRICES["views"], DYNAMIC_PRICES["comments"])
        await q.edit_message_text(txt, reply_markup=get_back_kb(uid), parse_mode=ParseMode.MARKDOWN)
    elif data == "enter_code":
        context.user_data["awaiting"] = "code"
        await q.edit_message_text(t(uid, "ask_code"), reply_markup=get_back_kb(uid))
    elif data == "add_acc":
        if len([k for k in accs if k != "_active"]) >= user.get("max_acc", 3):
            return await q.answer(f"الحد الأقصى {user.get('max_acc', 3)} حسابات!", show_alert=True)
        context.user_data["awaiting"] = "acc_user"
        await q.edit_message_text(t(uid, "ask_user"), reply_markup=get_back_kb(uid))
    elif data == "accs":
        kb = [[InlineKeyboardButton(f"👤 {k} ⭐{v.get('score',0)}", callback_data=f"sw_{k}")] for k, v in accs.items() if k != "_active"]
        kb.append([InlineKeyboardButton(t(uid, "add"), callback_data="add_acc")])
        kb.append([InlineKeyboardButton(t(uid, "back"), callback_data="back")])
        await q.edit_message_text(t(uid, "accs"), reply_markup=InlineKeyboardMarkup(kb))
    elif data.startswith("sw_"):
        accs["_active"] = data.split("_")[1]
        await start(update, context)
    elif data == "farm_menu":
        active = accs.get("_active")
        if not active: return await q.answer("أضف حساباً أولاً!", show_alert=True)
        is_f = accs[active].get("farming", False)
        kb = [[InlineKeyboardButton(t(uid, "stop") if is_f else t(uid, "start"), callback_data="stop_f" if is_f else "start_f")], [InlineKeyboardButton(t(uid, "back"), callback_data="back")]]
        await q.edit_message_text(f"حالة التجميع للحساب `{active}`:", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
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
        if not HAS_MPL: return await q.answer("الرسم البياني غير مدعوم في هذه البيئة.", show_alert=True)
        
        total = sum(v.get("score",0) for k,v in accs.items() if k != "_active")
        if not accs: return await q.edit_message_text("لا توجد حسابات.", reply_markup=get_back_kb(uid))
        
        labels = [k for k in accs.keys() if k != "_active"]
        scores = [accs[k].get("score", 0) for k in labels]
        
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(labels, scores, color="#3b82f6")
        ax.set_title(f"Total Score: {total}")
        buf = io.BytesIO(); plt.tight_layout(); plt.savefig(buf, format="png"); plt.close(); buf.seek(0)
        
        await q.message.reply_photo(photo=buf, caption="📊 إحصائيات حساباتك")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    aw = context.user_data.get("awaiting")
    accs = USER_ACCOUNTS.setdefault(str(uid), {})

    if aw == "manage_uid" and uid == OWNER_ID:
        target_id = text
        if target_id not in USERS: return await update.message.reply_text(t(uid, "user_not_found"))
        target_user = get_user(target_id)
        speed_txt = {"fast": "🚀 سريع", "normal": "⚖️ عادي", "slow": "🐢 بطيء"}.get(target_user.get("speed", "normal"))
        text_out = t(uid, "mu_title").format(target_id, len([k for k in USER_ACCOUNTS.get(target_id, {}) if k != '_active']), target_user.get("max_acc", 3), speed_txt, target_user.get("work_hours", 16))
        context.user_data.clear()
        await update.message.reply_text(text_out, reply_markup=get_manage_user_kb(target_id), parse_mode=ParseMode.MARKDOWN)
        return

    if aw == "mu_limit" and uid == OWNER_ID:
        try:
            limit = int(text)
            target_id = context.user_data.get("target_id")
            get_user(target_id)["max_acc"] = limit
            save_data()
            context.user_data.clear()
            await update.message.reply_text(t(uid, "limit_changed").format(limit), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(uid, "back"), callback_data=f"back_manage_{target_id}")]]))
        except: await update.message.reply_text("❌ أرسل رقماً صحيحاً.")
        return

    if aw == "mu_hours" and uid == OWNER_ID:
        try:
            hours = int(text)
            if hours > 24 or hours < 1: raise ValueError
            target_id = context.user_data.get("target_id")
            get_user(target_id)["work_hours"] = hours
            save_data()
            context.user_data.clear()
            await update.message.reply_text(t(uid, "hours_changed").format(hours), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(uid, "back"), callback_data=f"back_manage_{target_id}")]]))
        except: await update.message.reply_text("❌ أرسل رقماً صحيحاً بين 1 و 24.")
        return

    if aw == "gen_duration" and uid == OWNER_ID:
        seconds, desc = parse_duration(text)
        if not seconds: return await update.message.reply_text("❌ صيغة خاطئة. أرسل `5d` أو `10h` أو `1m`")
        c = str(uuid.uuid4())[:6].upper()
        CODES[c] = {"seconds": seconds, "used": False}
        save_data()
        context.user_data.clear()
        await update.message.reply_text(f"✅ الكود: `{c}`\n⏳ المدة: {desc}", parse_mode=ParseMode.MARKDOWN, reply_markup=get_back_kb(uid))
        return

    if aw == "add_channel" and uid == OWNER_ID:
        ch = text if text.startswith("@") or text.startswith("-") else "@" + text
        if ch not in CHANNELS: CHANNELS.append(ch); save_data()
        context.user_data.clear()
        await update.message.reply_text(t(uid, "ch_added"), reply_markup=get_back_kb(uid))
        return

    if aw == "code":
        if text in CODES and not CODES[text]["used"]:
            CODES[text]["used"] = True
            secs = CODES[text].get("seconds", 86400)
            get_user(uid)["exp"] = max(time.time(), get_user(uid).get("exp", 0)) + secs
            save_data()
            await update.message.reply_text(t(uid, "code_ok"))
            await start(update, context)
        else: await update.message.reply_text(t(uid, "code_bad"))
        context.user_data.clear()
    elif aw == "acc_user":
        context.user_data["temp_u"] = text
        context.user_data["awaiting"] = "acc_pass"
        await update.message.reply_text(t(uid, "ask_pass"))
    elif aw == "acc_pass":
        uname, pwd = context.user_data.pop("temp_u"), text
        context.user_data.clear()
        msg = await update.message.reply_text("⏳ جاري الدخول...")
        payload = {"operationName":"LoginAccount","variables":{"data":{"uniqueId":uname,"password":pwd,"authMethod":"local"}},"query":"mutation LoginAccount($data: TiktokInfo) { loginTiktok(data: $data) { accessToken user { score } } }"}
        r, res = await asyncio.to_thread(req, "", "", payload, "LoginAccount", False)
        if r and res and "data" in res:
            accs[uname] = {"token": res["data"]["loginTiktok"]["accessToken"], "csrf": r.headers.get("x-csrf-token",""), "score": res["data"]["loginTiktok"]["user"].get("score",0), "farming": False, "password": pwd, "proxy": proxy_pool.acquire()}
            accs["_active"] = uname
            save_data()
            await msg.edit_text("✅ تم الإضافة!")
            await start(update, context)
        else: await msg.edit_text("❌ فشل الدخول. تأكد من البيانات.")

# ==========================================
# 📤 استقبال الملفات لتحديث الكود
# ==========================================
async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != OWNER_ID: return
    
    aw = context.user_data.get("awaiting")
    if aw == "update_code":
        document = update.message.document
        if not document.file_name.endswith(".py"):
            return await update.message.reply_text(t(uid, "bad_file"))
            
        msg = await update.message.reply_text(t(uid, "updating"))
        
        try:
            file = await context.bot.get_file(document.file_id)
            current_script = os.path.abspath(__file__)
            
            if os.path.exists(current_script):
                os.remove(current_script)
                
            await file.download_to_drive(current_script)
            
            await msg.edit_text("✅ تم استبدال الملف بنجاح!\n🔄 جاري إعادة تشغيل البوت...")
            await asyncio.sleep(2) 
            
            os.execv(sys.executable, ['python'] + sys.argv)
            
        except Exception as e:
            await msg.edit_text(f"❌ حدث خطأ أثناء التحديث: {e}")
        context.user_data.clear()
        return

# ==========================================
# ⏱️ دالة تحويل النص إلى وقت
# ==========================================
def parse_duration(text):
    text = text.strip().lower()
    try:
        if text.endswith("h"): return float(text[:-1]) * 3600, f"{text[:-1]} ساعة"
        elif text.endswith("d"): return float(text[:-1]) * 86400, f"{text[:-1]} يوم"
        elif text.endswith("m"): return float(text[:-1]) * (30 * 86400), f"{text[:-1]} شهر"
        else: return float(text) * 86400, f"{text} يوم"
    except: return None, None

# ==========================================
# 👑 أوامر المطور
# ==========================================
async def cmd_setlimit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    try:
        tid = str(context.args[0])
        lim = int(context.args[1])
        if tid not in USERS: USERS[tid] = {"exp": 0, "lang": "ar", "max_acc": lim, "blocked": False, "starts": 0, "speed": "normal", "work_hours": 16}
        else: USERS[tid]["max_acc"] = lim
        save_data()
        await update.message.reply_text(f"✅ تم تعديل حد المستخدم `{tid}` لـ {lim}.", parse_mode=ParseMode.MARKDOWN)
    except: await update.message.reply_text("⚠️ الصيغة: `/setlimit USER_ID NUMBER`", parse_mode=ParseMode.MARKDOWN)

# ==========================================
# 🚀 دالة التشغيل الرئيسية
# ==========================================
async def post_init(app):
    # جلب البروكسيات في الخلفية عند بدء التشغيل
    asyncio.create_task(asyncio.to_thread(fetch_free_proxies))

def run_bot():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setlimit", cmd_setlimit))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    
    print(c("✅ Ultimate Bot is running...", f"{E1}{G}"))
    app.run_polling(drop_pending_updates=True)

def main():
    load_data()
    
    # Supervisor Loop: يمنع البوت من التوقف عند حدوث خطأ
    crashes = 0
    while True:
        try:
            run_bot()
            crashes = 0
        except KeyboardInterrupt:
            print(c("👋 Bot stopped manually.", Y))
            return
        except Exception as e:
            crashes += 1
            print(c(f"[Supervisor] 💥 Crash #{crashes}: {e}", r))
            traceback.print_exc()
            if "unauthorized" in str(e).lower() or "invalid token" in str(e).lower():
                print(c("❌ خطأ في التوكن! البوت سيتوقف.", r))
                time.sleep(60)
                continue
            time.sleep(min(5 * crashes, 60))

if __name__ == "__main__":
    def _sig(signum, frame):
        raise KeyboardInterrupt
    try: signal.signal(signal.SIGTERM, _sig)
    except: pass
    
    main()
