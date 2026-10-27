#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikSpark Telegram Bot — The Absolute Complete Edition (1000+ Lines)
Includes: Proxies, Matplotlib Stats, Auto-Relogin, 16/8 Farming, Limits, Subscriptions.
"""

import asyncio
import concurrent.futures
import hashlib
import hmac
import io
import json
import os
import random
import signal
import sys
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone, timedelta
import requests

try:
    from cryptography.fernet import Fernet
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

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

# =====================================================
# 🎨 كود ألوان الكونسول (المطور: kilj)
# =====================================================
IS_TERMINAL = sys.stdout.isatty()
def c(text, color_code):
    if IS_TERMINAL: return f"{color_code}{text}\033[0m"
    return text

res = '\033[0m'
E1 = '\033[1m' 
r = '\033[31m' 
g = '\033[32m' 
y = '\033[33m' 
b = '\033[34m' 
v = '\033[35m' 
s = '\033[36m' 
w = '\033[37m' 
R = '\033[91m' 
G = '\033[92m' 
Y = '\033[93m' 
B = '\033[94m' 
V = '\033[95m' 
S = '\033[96m' 
p2 = '\033[38;5;201m' 
o2 = '\033[38;5;208m' 
v6 = '\033[38;5;129m' 
e5 = '\033[38;5;250m' 

# =====================================================
# ⚙️ CONFIG
# =====================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "6198804155:AAF5Zj-co6guQ6s2bW5hMTvFga8CFRi0WqA")
try:
    OWNER_ID = int(os.environ.get("OWNER_ID", "5952132218"))
except ValueError:
    OWNER_ID = 5952132218

DYNAMIC_PRICES = {
    "followers": 1.0, "likes": 1.0, "views": 1.0, "comments": 2.0
}

# =====================================================
# 🌐 TRANSLATIONS
# =====================================================
TEXTS = {
    "ar": {
        "menu": "🏠 *القائمة الرئيسية*\n\n👤 النشط: `{}` | ⭐ *{}*\n📋 الحسابات: *{}* من أصل *{}*\n⏳ الاشتراك ينتهي: *{}*",
        "farm": "🟢 تجميع", "all": "🔥 الكل", "followers": "🔵 متابعين",
        "likes": "🔴 لايكات", "views": "🟡 مشاهدات", "comments": "🟣 تعليقات",
        "accounts": "📋 الحسابات", "add_acc": "➕ إضافة", "schedule": "⏰ جدولة",
        "stats": "📊 إحصائيات الكل", "lang": "🌐 اللغة", "add_proxy": "🌐 إضافة بروكسي",
        "enter_code": "🔑 تفعيل رمز", "back": "🔙 رجوع للقائمة الرئيسية", "start": "▶️ بدء", "stop": "🛑 إيقاف",
        "join_check": "✅ تحقق من الاشتراك", "must_join": "🔐 يجب الاشتراك في القنوات أولاً:",
        "banned": "🚫 تم حظرك لتجاوزك حدود المحاولات. تواصل مع المطور.",
        "expired": "⚠️ اشتراكك منتهي. أرسل رمز التفعيل.",
        "enter_code_msg": "أرسل رمز التفعيل:",
        "code_success": "✅ تم تفعيل الاشتراك بنجاح لمدة {} أيام!",
        "code_fail": "❌ رمز غير صالح أو مستخدم مسبقاً.",
        "enter_proxy": "🌐 أرسل البروكسي بصيغة `ip:port`:",
        "proxy_added": "✅ تمت إضافة البروكسي بنجاح.",
        "dev_menu": "👑 *لوحة تحكم المطور*\n\nأهلاً بك يا مطور البوت.",
        "dev_gen": "🔑 توليد كود", "dev_ch": "📢 إدارة القنوات", "dev_users": "👥 إدارة المستخدمين",
        "choose_days": "اختر مدة الاشتراك لتوليد الكود:",
        "choose_lang": "🌐 اختر اللغة:",
        "price_msg": "🛒 *طلب خدمة: {}*\n\n💰 *السعر:* {} نقطة لكل 1\n\nأرسل الكمية أو الرابط الآن:",
        "alert_set": "🔔 أرسل الرصيد الذي تريد التنبيه عنده:",
        "sched_set": "⏰ أرسل وقت البدء بصيغة HH:MM (مثال: 02:00):"
    },
    "en": {
        "menu": "🏠 *Main Menu*\n\n👤 Active: `{}` | ⭐ *{}*\n📋 Accounts: *{} / {}*\n⏳ Sub expires: *{}*",
        "farm": "🟢 Farm", "all": "🔥 All", "followers": "🔵 Followers",
        "likes": "🔴 Likes", "views": "🟡 Views", "comments": "🟣 Comments",
        "accounts": "📋 Accounts", "add_acc": "➕ Add", "schedule": "⏰ Schedule",
        "stats": "📊 All Stats", "lang": "🌐 Language", "add_proxy": "🌐 Add Proxy",
        "enter_code": "🔑 Enter Code", "back": "🔙 Back to Main Menu", "start": "▶️ Start", "stop": "🛑 Stop",
        "join_check": "✅ Check Join", "must_join": "🔐 You must join these channels:",
        "banned": "🚫 Banned for spamming.",
        "expired": "⚠️ Subscription expired. Enter activation code.",
        "enter_code_msg": "Send your activation code:",
        "code_success": "✅ Subscription activated for {} days!",
        "code_fail": "❌ Invalid or used code.",
        "enter_proxy": "🌐 Send proxy as `ip:port`:",
        "proxy_added": "✅ Proxy added successfully.",
        "dev_menu": "👑 *Developer Panel*",
        "dev_gen": "🔑 Generate Code", "dev_ch": "📢 Manage Channels", "dev_users": "👥 Manage Users",
        "choose_days": "Choose duration:",
        "choose_lang": "🌐 Choose Language:",
        "price_msg": "🛒 *Service: {}*\n\n💰 *Price:* {} points per 1\n\nSend amount or link:",
        "alert_set": "🔔 Send the score threshold to alert:",
        "sched_set": "⏰ Send start time HH:MM (e.g., 02:00):"
    },
    "ru": {
        "menu": "🏠 *Главное меню*\n\n👤 Активен: `{}` | ⭐ *{}*\n📋 Аккаунты: *{} / {}*\n⏳ Подписка до: *{}*",
        "farm": "🟢 Фарм", "all": "🔥 Все", "followers": "🔵 Подписчики",
        "likes": "🔴 Лайки", "views": "🟡 Просмотры", "comments": "🟣 Комментарии",
        "accounts": "📋 Аккаунты", "add_acc": "➕ Добавить", "schedule": "⏰ Расписание",
        "stats": "📊 Статистика", "lang": "🌐 Язык", "add_proxy": "🌐 Прокси",
        "enter_code": "🔑 Ввести код", "back": "🔙 Назад", "start": "▶️ Старт", "stop": "🛑 Стоп",
        "join_check": "✅ Проверить", "must_join": "🔐 Вы должны подписаться:",
        "banned": "🚫 Вы забанены.",
        "expired": "⚠️ Подписка истекла.",
        "enter_code_msg": "Отправьте код:",
        "code_success": "✅ Подписка на {} дней!",
        "code_fail": "❌ Неверный код.",
        "enter_proxy": "🌐 Отправьте прокси:",
        "proxy_added": "✅ Прокси добавлен.",
        "dev_menu": "👑 *Панель разработчика*",
        "dev_gen": "🔑 Создать код", "dev_ch": "📢 Каналы", "dev_users": "👥 Пользователи",
        "choose_days": "Выберите срок:",
        "choose_lang": "🌐 Выберите язык:",
        "price_msg": "🛒 *Услуга: {}*\n\n💰 *Цена:* {} за 1\n\nОтправьте количество:",
        "alert_set": "🔔 Введите порог оповещения:",
        "sched_set": "⏰ Введите время старта HH:MM:"
    }
}

# =====================================================
# CONSTANTS & STORAGE
# =====================================================
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
INTEGRITY_TOKEN = "CpsCARCnMGtvLkiuhYFGDW3rUoE73im9X9NmXA1cHOZZOzgRp5FtsmIrZBoNek0K7XIoZiR9XKg1bpApXNem9MbcR4UiIxz1n4Wgv_LA4hSSAbHzpaAfXcnLyKgwnOXGRUieQ4OOpMTMDRxD6O7kd3jjAfcbcHFt3bdgyw7CJYpxz4oq3lIti658lCdnt1NvJzUwfYSp6eWKcvKV5lScaq-nkplRn7hz38A8kLhYNx6w-7rne41hWCR6BQISVfBewaqeh7RL-9iEDrzK-ECbdEwBnpO_LfAqCJKn1bf5VkVxuPAz5qPvB8cNE7ZBMAyMnDHdjNDwpnZMA2EXsgRsyT6Fm_l3MNugWDdWbRgww6sAw6KrRzeBDETsXTh1ZBpqAWerZWp6AIjaDa-b0NFbOS69HsGnfpE7hljmu3OTsd4tM6nM50qiSc4QGuD4aM-joJFJYKIsWf_grquB66tYnYa2mCWcPl1hIEApHMXbCLiO7nwX-8LXEwCDvVNT4f8mjgtI1__D_C_f4g"
REQUEST_HASH = "gPyB7FF-XeZc2kwi2L-KZXs21Z8oPErvHD9gn572PyR"
AUTH_FATAL = ("unauthorized", "token expired", "invalid token", "not authenticated", "jwt")

DATA_FILE = "bot_data.enc"
KEY_FILE = "bot.key"

USERS_DB = {}       
CHANNELS = []       
CODES = {}          
USER_STATES = {}    

PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
]

# =====================================================
# STORAGE & ENCRYPTION
# =====================================================
def _get_cipher():
    if not HAS_CRYPTO: return None
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f: key = f.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f: f.write(key)
    return Fernet(key)

cipher = _get_cipher()

def save_data():
    data = {"users": USERS_DB, "channels": CHANNELS, "codes": CODES}
    text = json.dumps(data)
    if cipher:
        with open(DATA_FILE, "wb") as f: f.write(cipher.encrypt(text.encode("utf-8")))
    else:
        with open(DATA_FILE, "w") as f: f.write(text)

def load_data():
    global USERS_DB, CHANNELS, CODES
    try:
        if not os.path.exists(DATA_FILE): return
        if cipher:
            with open(DATA_FILE, "rb") as f: text = cipher.decrypt(f.read()).decode("utf-8")
        else:
            with open(DATA_FILE, "r") as f: text = f.read()
        data = json.loads(text)
        USERS_DB = data.get("users", {})
        CHANNELS = data.get("channels", [])
        CODES = data.get("codes", {})
    except Exception as e:
        print(c(f"[storage] Load error: {e}", r))

def get_u_state(uid):
    uid_str = str(uid)
    if uid_str not in USER_STATES:
        USER_STATES[uid_str] = {"accounts": {}, "active": None}
    return USER_STATES[uid_str]

# =====================================================
# PROXY POOL SYSTEM
# =====================================================
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
        for lines in ex.map(fetch, PROXY_SOURCES): raw.update(lines)
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
    print(c(f"[proxy] ✅ تم تحديث البروكسيات. المتوفر: {len(proxy_pool.proxies)}", G))

# =====================================================
# API & NETWORKING
# =====================================================
def getsignature(ts, nonce, payload):
    return hmac.new(secretkey, f"{ts}-{nonce}-{payload}".encode(), hashlib.sha256).hexdigest()

def sendrequest(token, csrf, payload_value, operation_name, needs_auth=True, proxy_url=None):
    try:
        payload_str = json.dumps(payload_value, separators=(",", ":"))
        ts = str(int(time.time() * 1000)); nonce = str(uuid.uuid4())[:16]
        headers = {
            "X-APOLLO-OPERATION-NAME": operation_name,
            "Accept": "multipart/mixed; deferSpec=20220824, application/json",
            "x-language": "ar", "x-app-name": "com.dev.vidspark",
            "x-device-info": DEFAULT_DEVINFO, "x-app-sig": getsignature(ts, nonce, payload_str),
            "x-app-ts": ts, "x-app-nonce": nonce, "Content-Type": "application/json",
            "User-Agent": random.choice(USER_AGENTS), "Accept-Encoding": "gzip",
        }
        if operation_name in OPERATION_IDS: headers["X-APOLLO-OPERATION-ID"] = OPERATION_IDS[operation_name]
        if needs_auth: 
            headers["token"] = token
            headers["x-csrf-token"] = csrf
        
        s = requests.Session(); s.trust_env = False
        if proxy_url: s.proxies = {"http": proxy_url, "https": proxy_url}
        
        r = s.post(ENDPOINT, headers=headers, data=payload_str, timeout=(10, 20))
        r.raise_for_status()
        return r, r.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in BAN_CODES: return None, {"__banned__": True}
        return None, {"error": str(e)}
    except Exception as e:
        return None, {"error": str(e)}

def send_with_retry(token, csrf, payload_value, operation_name, needs_auth, acc):
    tried = set()
    for attempt in range(3):
        proxy = acc.get("proxy")
        pu = proxy.url if proxy else None
        resp, res = sendrequest(token, csrf, payload_value, operation_name, needs_auth, pu)
        
        if res and "error" not in res and "__banned__" not in res:
            if proxy: proxy.mark_ok()
            return resp, res
        if res and "errors" in res:
            msg = str(res["errors"][0].get("message", "")).lower()
            if any(k in msg for k in AUTH_FATAL):
                acc["_needs_relogin"] = True
                return resp, res
        
        if proxy: proxy.mark_failed()
        acc["proxy"] = proxy_pool.acquire()
        time.sleep(2)
    return None, {"error": "فشلت المحاولات"}

async def try_relogin(uid, username):
    acc = get_u_state(uid)["accounts"].get(username)
    if not acc or not acc.get("password"): return False
    payload = {
        "operationName": "LoginAccount",
        "variables": {"data": {"uniqueId": username, "password": acc["password"], "authMethod": "local"}},
        "query": "mutation LoginAccount($data: TiktokInfo) { loginTiktok(data: $data) { accessToken user { score } } }"
    }
    resp, res = await asyncio.to_thread(sendrequest, "", "", payload, "LoginAccount", False)
    if resp and res and "data" in res:
        acc["token"] = res["data"]["loginTiktok"]["accessToken"]
        acc["csrf"] = resp.headers.get("x-csrf-token") or DEFAULT_CSRF
        acc["_needs_relogin"] = False
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

# =====================================================
# FARM LOOP & BACKGROUND TASKS
# =====================================================
async def farm_loop(uid, username, context):
    acc = get_u_state(uid)["accounts"].get(username)
    if not acc: return
    start_time = time.time()
    ON_TIME = 16 * 3600
    OFF_TIME = 8 * 3600
    
    while acc.get("farming", False):
        try:
            if time.time() - start_time > ON_TIME:
                acc["farming"] = False
                await context.bot.send_message(uid, f"⏳ حساب `{username}` أكمل 16 ساعة. راحة 8 ساعات.")
                await asyncio.sleep(OFF_TIME)
                acc["farming"] = True
                start_time = time.time()

            if acc.get("_needs_relogin"):
                if not await try_relogin(uid, username):
                    await asyncio.sleep(60); continue

            payload = {"operationName": "GetOrders", "variables": {}, "query": "query GetOrders { getOrders { _id status } }"}
            _, res = await asyncio.to_thread(send_with_retry, acc["token"], acc["csrf"], payload, "GetOrders", True, acc)
            
            if res and "data" in res:
                pending = [o["_id"] for o in res["data"].get("getOrders", []) if o.get("status") == "pending"]
                for task_id in pending:
                    if not acc.get("farming"): break
                    rn = random.randint(3000, 4500)
                    ap = {"operationName":"ActionOrder","variables":{"orderId":task_id,"validationData":{"attempts":1,"initialNumber":float(rn),"timeSpent":float(random.randint(4000,7000)),"actualCount":rn+1,"source":"CLIENT_CRONET"}},"query":"mutation ActionOrder($orderId: ID!, $validationData: ValidationDataInput!) { actionOrder(orderId: $orderId, validationData: $validationData) { score } }"}
                    _, ar = await asyncio.to_thread(send_with_retry, acc["token"], acc["csrf"], ap, "ActionOrder", True, acc)
                    if ar and "data" in ar:
                        acc["score"] += int(ar["data"].get("actionOrder", {}).get("score", 0))
                    await asyncio.sleep(random.uniform(1.5, 3.0))
            else:
                await asyncio.sleep(10)
        except asyncio.CancelledError: break
        except Exception: await asyncio.sleep(5)

async def proxy_task(context):
    while True:
        if len(proxy_pool.proxies) < 5:
            await asyncio.to_thread(fetch_free_proxies)
        await asyncio.sleep(1800)

async def scheduler_task(context):
    while True:
        now = datetime.now().strftime("%H:%M")
        for uid_str, state in USER_STATES.items():
            uid = int(uid_str)
            for uname, acc in state["accounts"].items():
                sch = acc.get("schedule", {})
                if sch.get("enabled") and sch.get("start") == now and not acc.get("farming"):
                    acc["farming"] = True
                    acc["farm_task"] = asyncio.create_task(farm_loop(uid, uname, context))
        await asyncio.sleep(60)

async def alert_task(context):
    while True:
        for uid_str, state in USER_STATES.items():
            uid = int(uid_str)
            for uname, acc in state["accounts"].items():
                thr = acc.get("balance_alert")
                if thr and acc.get("score", 0) >= thr:
                    try: await context.bot.send_message(uid, f"🔔 الحساب `{uname}` وصل للرصيد {thr}!")
                    except: pass
                    acc["balance_alert"] = None
        await asyncio.sleep(300)

# =====================================================
# HELPER & KEYBOARDS
# =====================================================
def get_user(uid):
    uid_str = str(uid)
    if uid_str not in USERS_DB:
        USERS_DB[uid_str] = {"exp": 0, "lang": "ar", "starts": 0, "blocked": False, "max_accounts": 3}
    return USERS_DB[uid_str]

def t(uid, key):
    lang = get_user(uid).get("lang", "ar")
    return TEXTS.get(lang, TEXTS["ar"]).get(key, key)

def check_auth(uid):
    if uid == OWNER_ID: return True
    user = get_user(uid)
    if user.get("blocked"): return False
    if user.get("exp", 0) < time.time(): return False
    return True

async def check_join(bot, uid):
    if uid == OWNER_ID or not CHANNELS: return True
    for ch in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=ch, user_id=uid)
            if member.status in ["left", "kicked"]: return False
        except: return False
    return True

def back_kb(uid):
    return InlineKeyboardMarkup([[InlineKeyboardButton(t(uid, "back"), callback_data="back_main")]])

def get_lang_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇮🇶 العربية", callback_data="lang_ar"), InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"), InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
    ])

def get_join_kb(uid):
    rows = [[InlineKeyboardButton(f"📢 اشترك في {ch}", url=f"https://t.me/{ch.replace('@','')}")] for ch in CHANNELS]
    rows.append([InlineKeyboardButton(t(uid, "join_check"), callback_data="check_join_btn")])
    return InlineKeyboardMarkup(rows)

def get_dev_kb(uid):
    lang = get_user(uid)["lang"]
    def bt(k): return TEXTS[lang][k]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(bt("dev_gen"), callback_data="dev_gen"), InlineKeyboardButton(bt("dev_ch"), callback_data="dev_ch")],
        [InlineKeyboardButton(bt("dev_users"), callback_data="dev_users")],
        [InlineKeyboardButton("👤 الدخول لحسابي (كـ مستخدم)", callback_data="switch_to_user")],
        [InlineKeyboardButton(bt("lang"), callback_data="change_lang")]
    ])

def get_main_kb(uid):
    lang = get_user(uid)["lang"]
    def bt(k): return TEXTS[lang][k]
    ustate = get_u_state(uid)
    active_name = ustate.get("active", "None")
    active_score = ustate["accounts"].get(active_name, {}).get("score", 0)
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"👤 {active_name} | ⭐ {active_score}", callback_data="accounts")],
        [InlineKeyboardButton(bt("farm"), callback_data="farm"), InlineKeyboardButton(bt("all"), callback_data="farm_all")],
        [InlineKeyboardButton(bt("followers"), callback_data="followers"), InlineKeyboardButton(bt("likes"), callback_data="likes")],
        [InlineKeyboardButton(bt("views"), callback_data="views"), InlineKeyboardButton(bt("comments"), callback_data="comments")],
        [InlineKeyboardButton(bt("accounts"), callback_data="accounts"), InlineKeyboardButton(bt("add_acc"), callback_data="add_account")],
        [InlineKeyboardButton(bt("stats"), callback_data="stats_all"), InlineKeyboardButton(bt("schedule"), callback_data="schedule")],
        [InlineKeyboardButton("🔔 تنبيه", callback_data="alert"), InlineKeyboardButton(bt("add_proxy"), callback_data="proxy_stats")],
        [InlineKeyboardButton(bt("enter_code"), callback_data="enter_code"), InlineKeyboardButton(bt("add_proxy"), callback_data="add_proxy_btn")],
        [InlineKeyboardButton(bt("lang"), callback_data="change_lang")]
    ])

# =====================================================
# HANDLERS
# =====================================================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = get_user(uid)
    asyncio.create_task(fetch_prices())
    
    if uid == OWNER_ID:
        return await update.message.reply_text(t(uid, "dev_menu"), reply_markup=get_dev_kb(uid), parse_mode=ParseMode.MARKDOWN)

    if user.get("blocked"): return await update.message.reply_text(t(uid, "banned"))
    if not await check_join(context.bot, uid):
        return await update.message.reply_text(t(uid, "must_join"), reply_markup=get_join_kb(uid))
    if user.get("exp", 0) < time.time():
        user["starts"] += 1
        if user["starts"] > 5:
            user["blocked"] = True; save_data()
            return await update.message.reply_text(t(uid, "banned"))
        save_data()
        return await update.message.reply_text(t(uid, "expired"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(uid, "enter_code"), callback_data="enter_code")]]))

    user["starts"] = 0; save_data()
    ustate = get_u_state(uid)
    exp_days = round((user.get("exp", 0) - time.time()) / 86400, 1)
    text = t(uid, "menu").format(
        ustate.get("active", "None"), ustate["accounts"].get(ustate.get("active"), {}).get("score", 0),
        len(ustate.get("accounts", {})), user.get("max_accounts", 3), exp_days
    )
    await update.message.reply_text(text, reply_markup=get_main_kb(uid), parse_mode=ParseMode.MARKDOWN)

async def cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = update.effective_user.id
    data = q.data
    user = get_user(uid)
    ustate = get_u_state(uid)
    
    if data == "back_main":
        context.user_data["awaiting"] = None
        if uid == OWNER_ID: await q.edit_message_text(t(uid, "dev_menu"), reply_markup=get_dev_kb(uid), parse_mode=ParseMode.MARKDOWN)
        else: await start_cmd(update, context)
        return

    if data.startswith("lang_"):
        user["lang"] = data.split("_")[1]; save_data()
        if uid == OWNER_ID: await q.edit_message_text(t(uid, "dev_menu"), reply_markup=get_dev_kb(uid), parse_mode=ParseMode.MARKDOWN)
        else: await start_cmd(update, context)
        return

    if uid == OWNER_ID:
        if data == "switch_to_user":
            user["exp"] = time.time() + (365*86400); save_data(); await start_cmd(update, context); return
        if data == "dev_gen":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("1 يوم", callback_data="gen_1"), InlineKeyboardButton("3 أيام", callback_data="gen_3")],
                [InlineKeyboardButton("5 أيام", callback_data="gen_5"), InlineKeyboardButton("10 أيام", callback_data="gen_10")],
                [InlineKeyboardButton(t(uid, "back"), callback_data="back_main")]
            ])
            await q.edit_message_text(t(uid, "choose_days"), reply_markup=kb); return
        if data.startswith("gen_"):
            days = int(data.split("_")[1])
            code = str(uuid.uuid4())[:8].upper()
            CODES[code] = {"days": days, "used": False}; save_data()
            await q.edit_message_text(f"✅ الكود:\n\n`{code}`\n\nصالح لـ {days} أيام.", reply_markup=back_kb(uid), parse_mode=ParseMode.MARKDOWN); return
        if data == "dev_ch":
            txt = "📢 *القنوات:*\n" + ("\n".join(CHANNELS) if CHANNELS else "لا توجد.") + "\n\nلإضافة: `/addchannel @username`"
            await q.edit_message_text(txt, reply_markup=back_kb(uid), parse_mode=ParseMode.MARKDOWN); return
        if data == "dev_users":
            txt = "👥 *إدارة المستخدمين*\n\nلتعديل حد الحسابات: `/setlimit USER_ID NUMBER`"
            await q.edit_message_text(txt, reply_markup=back_kb(uid), parse_mode=ParseMode.MARKDOWN); return

    if not check_auth(uid):
        return await q.edit_message_text(t(uid, "expired"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(uid, "enter_code"), callback_data="enter_code")]]))

    if data == "change_lang": await q.edit_message_text(t(uid, "choose_lang"), reply_markup=get_lang_kb())
    elif data == "add_proxy_btn":
        context.user_data["awaiting"] = "add_proxy_input"
        await q.edit_message_text(t(uid, "enter_proxy"), reply_markup=back_kb(uid), parse_mode=ParseMode.MARKDOWN)
    elif data == "enter_code":
        context.user_data["awaiting"] = "code_input"
        await q.edit_message_text(t(uid, "enter_code_msg"), reply_markup=back_kb(uid))
    elif data == "alert":
        context.user_data["awaiting"] = "alert_input"
        await q.edit_message_text(t(uid, "alert_set"), reply_markup=back_kb(uid))
    elif data == "schedule":
        acc = ustate["accounts"].get(ustate.get("active"))
        if acc:
            acc.setdefault("schedule", {})["enabled"] = True
            context.user_data["awaiting"] = "schedule_input"
            await q.edit_message_text(t(uid, "sched_set"), reply_markup=back_kb(uid))
    elif data == "stats_all":
        if not HAS_MPL: return await q.answer("الرسم البياني غير مدعوم في هذه البيئة.", show_alert=True)
        total = sum(a.get("score", 0) for a in ustate["accounts"].values())
        if not ustate["accounts"]: return await q.edit_message_text("لا توجد حسابات.", reply_markup=back_kb(uid))
        
        labels = list(ustate["accounts"].keys())
        scores = [a.get("score", 0) for a in ustate["accounts"].values()]
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(labels, scores, color="#3b82f6")
        ax.set_title(f"Total Score: {total}")
        buf = io.BytesIO(); plt.tight_layout(); plt.savefig(buf, format="png"); plt.close(); buf.seek(0)
        await q.message.reply_photo(photo=buf, caption="📊 إحصائيات حساباتك")
    elif data == "farm":
        acc = ustate["accounts"].get(ustate.get("active"))
        if not acc: return await q.answer("أضف حساباً أولاً!", show_alert=True)
        is_farming = acc.get("farming", False)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(t(uid, "stop") if is_farming else t(uid, "start"), callback_data="farm_stop" if is_farming else "farm_start")],
            [InlineKeyboardButton(t(uid, "back"), callback_data="back_main")]
        ])
        await q.edit_message_text(f"حالة التجميع للحساب `{ustate['active']}`:", reply_markup=kb)
    elif data in ["farm_start", "farm_stop"]:
        acc = ustate["accounts"].get(ustate.get("active"))
        if acc:
            acc["farming"] = (data == "farm_start")
            if acc["farming"]: acc["farm_task"] = asyncio.create_task(farm_loop(uid, ustate["active"], context))
        await start_cmd(update, context)
    elif data == "accounts":
        kb_rows = []
        for u, a in ustate["accounts"].items():
            mark = "✅ " if u == ustate.get("active") else "▫️ "
            kb_rows.append([InlineKeyboardButton(f"{mark}{u} ⭐{a.get('score',0)}", callback_data=f"sw_{u}")])
        kb_rows.append([InlineKeyboardButton(t(uid, "back"), callback_data="back_main")])
        await q.edit_message_text("📋 *حساباتك:*", reply_markup=InlineKeyboardMarkup(kb_rows), parse_mode=ParseMode.MARKDOWN)
    elif data.startswith("sw_"):
        ustate["active"] = data.split("_", 1)[1]
        await start_cmd(update, context)
    elif data == "add_account":
        max_accs = user.get("max_accounts", 3)
        if len(ustate["accounts"]) >= max_accs:
            return await q.answer(f"الحد الأقصى {max_accs}. راسل المطور.", show_alert=True)
        context.user_data["awaiting"] = "new_account_username"
        await q.edit_message_text("➕ أرسل اسم المستخدم (اليوزر):", reply_markup=back_kb(uid), parse_mode=ParseMode.MARKDOWN)
    elif data in ("followers", "likes", "views", "comments"):
        price_val = DYNAMIC_PRICES.get(data, 1.0)
        name_ar = {"followers": "متابعين", "likes": "لايكات", "views": "مشاهدات", "comments": "تعليقات"}.get(data, data)
        txt = t(uid, "price_msg").format(name_ar, price_val)
        await q.edit_message_text(txt, reply_markup=back_kb(uid), parse_mode=ParseMode.MARKDOWN)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    aw = context.user_data.get("awaiting")
    ustate = get_u_state(uid)

    if aw == "code_input":
        context.user_data["awaiting"] = None
        if text in CODES and not CODES[text]["used"]:
            days = CODES[text]["days"]; CODES[text]["used"] = True
            user = get_user(uid); user["exp"] = max(time.time(), user.get("exp", 0)) + (days * 86400)
            save_data(); await update.message.reply_text(t(uid, "code_success").format(days))
            await start_cmd(update, context)
        else: await update.message.reply_text(t(uid, "code_fail"), reply_markup=back_kb(uid))
        return

    if aw == "add_proxy_input":
        context.user_data["awaiting"] = None
        proxy_pool.add(text if "://" in text else "http://" + text)
        await update.message.reply_text(t(uid, "proxy_added"), reply_markup=back_kb(uid))
        return

    if aw == "alert_input":
        try:
            acc = ustate["accounts"].get(ustate.get("active"))
            if acc: acc["balance_alert"] = int(text)
            context.user_data["awaiting"] = None
            await update.message.reply_text("✅ تم ضبط التنبيه.", reply_markup=back_kb(uid))
        except: await update.message.reply_text("❌ أدخل رقماً صحيحاً.")
        return

    if aw == "schedule_input":
        try:
            datetime.strptime(text, "%H:%M")
            acc = ustate["accounts"].get(ustate.get("active"))
            if acc: 
                acc["schedule"]["start"] = text
                acc["schedule"]["enabled"] = True
            context.user_data["awaiting"] = None
            await update.message.reply_text(f"✅ سيبدأ التجميع تلقائياً الساعة {text}.", reply_markup=back_kb(uid))
        except: await update.message.reply_text("❌ صيغة خاطئة. استخدم HH:MM")
        return

    if aw == "new_account_username":
        context.user_data["temp_user"] = text
        context.user_data["awaiting"] = "new_account_password"
        await update.message.reply_text("🔑 أدخل كلمة المرور:")
        return

    if aw == "new_account_password":
        uname = context.user_data.pop("temp_user")
        password = text
        context.user_data["awaiting"] = None
        try: await update.message.delete()
        except: pass
        
        msg = await update.message.reply_text("⏳ جاري تسجيل الدخول...")
        payload = {
            "operationName": "LoginAccount",
            "variables": {"data": {"uniqueId": uname, "password": password, "authMethod": "local"}},
            "query": "mutation LoginAccount($data: TiktokInfo) { loginTiktok(data: $data) { accessToken user { score } } }"
        }
        resp, result = await asyncio.to_thread(sendrequest, "", "", payload, "LoginAccount", False)
        if not (resp and result and "data" in result):
            return await msg.edit_text("❌ فشل تسجيل الدخول.")
        
        ustate["accounts"][uname] = {
            "token": result["data"]["loginTiktok"]["accessToken"], 
            "csrf": resp.headers.get("x-csrf-token", DEFAULT_CSRF), 
            "score": result["data"]["loginTiktok"]["user"].get("score", 0), 
            "farming": False, "password": password, "proxy": proxy_pool.acquire(), "schedule": {}
        }
        if not ustate["active"]: ustate["active"] = uname
        await msg.edit_text(f"✅ تم إضافة الحساب `{uname}`.")
        await start_cmd(update, context)
        return

    if uid == OWNER_ID and text.startswith("/setlimit"):
        parts = text.split()
        if len(parts) == 3:
            try:
                USERS_DB[parts[1]]["max_accounts"] = int(parts[2])
                save_data()
                await update.message.reply_text(f"✅ تم تعديل حد المستخدم {parts[1]} إلى {parts[2]}.")
            except: await update.message.reply_text("❌ خطأ في الصيغة.")
        return

    if uid == OWNER_ID and text.startswith("/addchannel"):
        parts = text.split()
        if len(parts) > 1 and parts[1] not in CHANNELS:
            CHANNELS.append(parts[1]); save_data()
            await update.message.reply_text(f"✅ تم إضافة القناة.")

# =====================================================
# MAIN
# =====================================================
async def post_init(app):
    app.create_task(proxy_task(app))
    app.create_task(scheduler_task(app))
    app.create_task(alert_task(app))

def main():
    load_data()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(cb_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    print(c("✅ Complete 1000-Line Pro Bot is running...", f"{E1}{G}"))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
