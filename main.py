# ═══════════════════════════════════════════════════════════
#  📦 المكتبات
# ═══════════════════════════════════════════════════════════

import os
import time
import json
import re
import asyncio
import logging
from datetime import date
from pathlib import Path

import requests
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile,
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)
from telegram.error import TelegramError


# ═══════════════════════════════════════════════════════════
#  ⚙️ الإعدادات
# ═══════════════════════════════════════════════════════════

BOT_TOKEN = (
    os.getenv("BOT_TOKEN")
    or os.getenv("TELEGRAM_BOT_TOKEN")
    or os.getenv("TELEGRAM_TOKEN")
    or os.getenv("TOKEN")
    or ""
)

ADMIN_ID = int(os.getenv("ADMIN_ID") or "5952132218")

DEV_USERNAME = "Mohammed"
DEV_LINK     = "https://t.me/c76xu"

CHANNEL_USERNAME = "@c2ccm"

# اليوزر الذي يظهر تحت كل فيديو
VIDEO_CREDIT = "@c76xu"

FAKE_USERS_COUNT = 0   # ← ضع 10000 إذا أردت عرضاً وهمياً في الواجهة


# ═══════════════════════════════════════════════════════════
#  🌍 اللغات
# ═══════════════════════════════════════════════════════════

DEFAULT_LANG = "ar"

LANGUAGES = {
    "ar": {
        "start": (
            "• اهلا بك اخي في بوت تحميل من تيك توك 🐿️.\n"
            "• فقط ارسل الرابط وسيتم ارسال المقطع بدون علامةه مائيةه 🤍.\n"
            ". — — — — — — — — — — .\n"
            "• Tele : {channel} | @c76xu ."
        ),
        "dev_btn": "• المطور .",
        "fetching": "⏳ جاري جلب الفيديو...",
        "fetch_failed": "❌ فشل جلب الفيديو. جرب رابطاً آخر.",
        "download_failed": "⚠️ تعذر تحميل الفيديو (حجم كبير أو رابط معطوب)",
        "send_failed": "⚠️ فشل إرسال الفيديو: {err}",
        "video_title": "العنوان",
        "video_author": "الاسم",
        "video_id": "المعرف",
        "admin_welcome": "🤍 | اهلا بك\n🤍 | اليك قائمه الاوامر",
        "bot_locked": "عذرا البوت يخضع للتحديث الان",
        "not_admin": "هذا الأمر للمشرفين فقط ⚠️",
        "users_count": "👥 عدد الاعضاء: {n}",
        "back_btn": "• الصفحه الرئيسيه",
        "cancel_btn": "الغاء",
    },
    "en": {
        "start": (
            "• Welcome to the TikTok Downloader Bot 🐿️.\n"
            "• Just send the link, and I'll send the video without watermark 🤍.\n"
            ". — — — — — — — — — — .\n"
            "• Tele : {channel} | @c76xu ."
        ),
        "dev_btn": "• Developer .",
        "fetching": "⏳ Fetching video...",
        "fetch_failed": "❌ Failed to fetch video. Try another link.",
        "download_failed": "⚠️ Could not download video (too large or broken link)",
        "send_failed": "⚠️ Failed to send video: {err}",
        "video_title": "Title",
        "video_author": "Author",
        "video_id": "ID",
        "admin_welcome": "🤍 | Welcome\n🤍 | Commands Menu",
        "bot_locked": "Sorry, the bot is under maintenance.",
        "not_admin": "This command is for admins only ⚠️",
        "users_count": "👥 Users count: {n}",
        "back_btn": "• Main Menu",
        "cancel_btn": "Cancel",
    },
    "ru": {
        "start": (
            "• Добро пожаловать в бот загрузки из TikTok 🐿️.\n"
            "• Просто отправьте ссылку, и я пришлю видео без водяного знака 🤍.\n"
            ". — — — — — — — — — — .\n"
            "• Tele : {channel} | @c76xu ."
        ),
        "dev_btn": "• Разработчик .",
        "fetching": "⏳ Получаю видео...",
        "fetch_failed": "❌ Не удалось получить видео. Попробуйте другую ссылку.",
        "download_failed": "⚠️ Не удалось скачать видео (слишком большое или битая ссылка)",
        "send_failed": "⚠️ Ошибка отправки видео: {err}",
        "video_title": "Название",
        "video_author": "Автор",
        "video_id": "ID",
        "admin_welcome": "🤍 | Добро пожаловать\n🤍 | Меню команд",
        "bot_locked": "Извините, бот на обновлении.",
        "not_admin": "Эта команда только для админов ⚠️",
        "users_count": "👥 Пользователей: {n}",
        "back_btn": "• Главное меню",
        "cancel_btn": "Отмена",
    },
    "fr": {
        "start": (
            "• Bienvenue sur le bot TikTok 🐿️.\n"
            "• Envoyez simplement le lien, je vous enverrai la vidéo sans filigrane 🤍.\n"
            ". — — — — — — — — — — .\n"
            "• Tele : {channel} | @c76xu ."
        ),
        "dev_btn": "• Développeur .",
        "fetching": "⏳ Récupération de la vidéo...",
        "fetch_failed": "❌ Échec de récupération. Essayez un autre lien.",
        "download_failed": "⚠️ Impossible de télécharger (trop volumineux ou lien cassé)",
        "send_failed": "⚠️ Échec d'envoi: {err}",
        "video_title": "Titre",
        "video_author": "Auteur",
        "video_id": "ID",
        "admin_welcome": "🤍 | Bienvenue\n🤍 | Menu des commandes",
        "bot_locked": "Le bot est en maintenance.",
        "not_admin": "Commande réservée aux admins ⚠️",
        "users_count": "👥 Utilisateurs : {n}",
        "back_btn": "• Menu principal",
        "cancel_btn": "Annuler",
    },
}


def get_lang(update) -> str:
    if not update or not update.effective_user:
        return DEFAULT_LANG
    code = (update.effective_user.language_code or "").lower()
    if code in LANGUAGES:
        return code
    base = code.split("-")[0]
    if base in LANGUAGES:
        return base
    return DEFAULT_LANG


def tr(key: str, lang: str, **kwargs) -> str:
    texts = LANGUAGES.get(lang) or LANGUAGES[DEFAULT_LANG]
    txt = texts.get(key) or LANGUAGES[DEFAULT_LANG].get(key) or key
    try:
        return txt.format(**kwargs) if kwargs else txt
    except (KeyError, IndexError):
        return txt


# ═══════════════════════════════════════════════════════════
#  🔧 ثوابت
# ═══════════════════════════════════════════════════════════

STATE_FILE  = "state.json"
USERS_FILE  = "abbas.json"
MAX_FILE_MB = 48
BROADCAST_DELAY = 0.05
MAX_SESSIONS = 500
KEEP_SESSIONS = 100

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("bottik")


# ═══════════════════════════════════════════════════════════
#  💾 التخزين
# ═══════════════════════════════════════════════════════════

def _default_state() -> dict:
    return {
        "bot_locked": False,
        "notifications": True,
        "sub_enabled": False,
        "sub_channel": "",
        "sub_link": "",
        "start_message": "",
        "admins": [],
        "stats": {
            "admin_messages": 0,
            "user_messages": 0,
            "today_date": "",
            "today_users": [],
        },
        "sessions": {},
    }


def load_state() -> dict:
    p = Path(STATE_FILE)
    base = _default_state()
    if not p.exists():
        return base
    try:
        with open(p, "r", encoding="utf-8") as f:
            s = json.load(f)
        base.update(s)
        base["stats"].update(_default_state()["stats"])
        if not isinstance(base.get("sessions"), dict):
            base["sessions"] = {}
        if not isinstance(base.get("admins"), list):
            base["admins"] = []
        return base
    except Exception:
        return base


def save_state(state: dict) -> None:
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"save_state: {e}")


def load_users() -> list:
    p = Path(USERS_FILE)
    if not p.exists():
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        return [int(l.strip()) for l in lines if l.strip().lstrip("-").isdigit()]
    except Exception:
        return []


def save_users(users: list) -> None:
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(str(u) for u in users))
            if users:
                f.write("\n")
    except Exception as e:
        logger.error(f"save_users: {e}")


# ═══════════════════════════════════════════════════════════
#  🎵 تيك توك
# ═══════════════════════════════════════════════════════════

TIKTOK_RE = re.compile(
    r'https?://(?:www\.)?(?:tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com|'
    r'm\.tiktok\.com)/\S+',
    re.IGNORECASE,
)

USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-A105F) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "SamsungBrowser/18.0 Chrome/99.0.4844.88 Mobile Safari/537.36"
)


def extract_tiktok_url(text: str):
    if not text:
        return None
    m = TIKTOK_RE.search(text)
    return m.group(0) if m else None


def _fix_url(u: str, base: str = "https://www.tikwm.com") -> str:
    if not u:
        return ""
    return u if u.startswith("http") else base + u


async def fetch_tiktok(url: str):
    for fn in (_try_tikwm, _try_lovetik):
        info = await fn(url)
        if info and info.get("video_no_wm"):
            return info
    return None


async def _try_tikwm(url: str):
    try:
        r = await asyncio.to_thread(
            requests.post,
            "https://www.tikwm.com/api/",
            data={"url": url, "hd": "1"},
            timeout=20,
        )
        if r.status_code != 200:
            return None
        j = r.json()
        if j.get("code") != 0 or not j.get("data"):
            return None
        d = j["data"]
        a = d.get("author") or {}
        return {
            "video_no_wm": _fix_url(d.get("play")),
            "video_wm":    _fix_url(d.get("wmplay") or d.get("play")),
            "audio":       _fix_url(d.get("music")),
            "title":       d.get("title", "") or "",
            "author_id":   a.get("unique_id", "") or "",
            "author_name": a.get("nickname", "") or "",
        }
    except Exception as e:
        logger.warning(f"tikwm: {e}")
        return None


async def _try_lovetik(url: str):
    headers = {
        "origin": "https://lovetik.com",
        "referer": "https://lovetik.com/",
        "user-agent": USER_AGENT,
    }
    try:
        r = await asyncio.to_thread(
            requests.post,
            "https://lovetik.com/api/ajax/search",
            data={"query": url},
            headers=headers,
            timeout=20,
        )
        if r.status_code != 200:
            return None
        j = r.json()
        links = j.get("links") or []
        if not links:
            return None
        no_wm = links[0].get("a", "")
        wm = links[3].get("a", "") if len(links) > 3 else no_wm
        return {
            "video_no_wm": no_wm,
            "video_wm":    wm,
            "audio":       no_wm,
            "title":       j.get("desc", "") or "",
            "author_id":   j.get("author", "") or "",
            "author_name": j.get("author_name", "") or "",
        }
    except Exception as e:
        logger.warning(f"lovetik: {e}")
        return None


async def download_to_file(url: str, path: str, max_mb: int = 48) -> bool:
    if not url:
        return False
    try:
        def _dl():
            with requests.get(url, stream=True, timeout=60,
                              headers={"user-agent": USER_AGENT}) as r:
                r.raise_for_status()
                total = 0
                with open(path, "wb") as f:
                    for chunk in r.iter_content(64 * 1024):
                        if not chunk:
                            continue
                        total += len(chunk)
                        if total > max_mb * 1024 * 1024:
                            raise ValueError(f"الملف أكبر من {max_mb}MB")
                        f.write(chunk)
            return True
        return await asyncio.to_thread(_dl)
    except Exception as e:
        logger.error(f"download {url}: {e}")
        return False


# ═══════════════════════════════════════════════════════════
#  🌐 الحالة العامة
# ═══════════════════════════════════════════════════════════

STATE = load_state()
USERS = load_users()


def is_admin(uid: int) -> bool:
    return uid == ADMIN_ID or uid in STATE["admins"]


def persist() -> None:
    save_state(STATE)


def persist_users() -> None:
    save_users(USERS)


def add_user(uid: int) -> bool:
    if uid in USERS:
        return False
    USERS.append(uid)
    persist_users()
    return True


def bump_stats(is_admin_user: bool) -> None:
    st = STATE["stats"]
    if is_admin_user:
        st["admin_messages"] += 1
    else:
        st["user_messages"] += 1
    persist()


def track_today_user(uid: int) -> None:
    st = STATE["stats"]
    today = date.today().isoformat()
    if st["today_date"] != today:
        st["today_date"] = today
        st["today_users"] = []
    if uid not in st["today_users"]:
        st["today_users"].append(uid)
        persist()


def cleanup_sessions() -> None:
    sess = STATE["sessions"]
    if len(sess) > MAX_SESSIONS:
        keys = list(sess.keys())[-KEEP_SESSIONS:]
        STATE["sessions"] = {k: sess[k] for k in keys}
        persist()


# ═══════════════════════════════════════════════════════════
#  🎛️ أزرار
# ═══════════════════════════════════════════════════════════

def btn(text, data=None, url=None):
    if url:
        return InlineKeyboardButton(text, url=url)
    return InlineKeyboardButton(text, callback_data=data)


def back_kb():
    return InlineKeyboardMarkup([[btn("• الصفحه الرئيسيه", "bak")]])


def cancel_kb():
    return InlineKeyboardMarkup([[btn("الغاء", "bak")]])


def admin_menu_kb():
    skor = "مفعل ✅" if STATE["sub_enabled"] else "معطل ⚠️"
    return InlineKeyboardMarkup([
        [btn("- قفل البوت .", "abcd"), btn("- فتح البوت .", "abcde")],
        [btn("- اعضاء البوت .", "userd")],
        [btn("- تفعيل التنبيه .", "ont"), btn("- تعطيل التنبيه .", "oft")],
        [btn("- قسم الاذاعه .", "for")],
        [btn("- قائمه الاشتراك .", "channel"),
         btn(f"- الاشتراك ({skor}) .", "off")],
        [btn("- نسخه احتياطيه .", "file"),
         btn("- رفع النسخه .", "up")],
        [btn("- الاحصائيات .", "pannel"),
         btn("- قسم الادمن .", "lIllabbas")],
        [btn("- التعديلات .", "xxxtentacionllllo")],
        [btn("- كليشه /start .", "editstart")],
    ])


ADMIN_HEADER = (
    "-•\n"
    "🤍 | اهلا بك\n"
    "🤍 | اليك قائمه الاوامر\n\n"
    f"dev: {DEV_USERNAME}  || 🇮🇶"
)


# ═══════════════════════════════════════════════════════════
#  🔒 فحص الاشتراك
# ═══════════════════════════════════════════════════════════

async def subscription_ok(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not STATE["sub_enabled"]:
        return True
    uid = update.effective_user.id
    if is_admin(uid):
        return True
    ch = STATE["sub_channel"]
    if not ch:
        return True
    try:
        m = await context.bot.get_chat_member(chat_id=ch, user_id=uid)
        if m.status in ("left", "kicked"):
            link = STATE["sub_link"] or ""
            txt = (
                "»  عليك الاشتراك في قناة تحديثات البوت اولا 📨\n"
                "»  ليمكنك استخدام البوت  🔊\n"
                "»  اشترك ثم ارسل { /start }\n"
                f"»  [اضغط هنا للاشتراك في القناة]({link})"
            )
            kb = None
            if link:
                kb = InlineKeyboardMarkup([[btn("اضغط هنا للاشتراك", url=link)]])
            await update.effective_message.reply_text(
                txt, parse_mode="Markdown",
                disable_web_page_preview=True, reply_markup=kb,
            )
            return False
    except TelegramError as e:
        logger.warning(f"sub check: {e}")
    return True


# ═══════════════════════════════════════════════════════════
#  🚀 /start
# ═══════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    uid = update.effective_user.id
    uname = update.effective_user.username or "بلا معرف"
    lang = get_lang(update)

    is_new = add_user(uid)
    if is_new and not is_admin(uid):
        try:
            await context.bot.send_message(
                ADMIN_ID,
                f"٭ تم دخول شخص جديد الى البوت 👾\n\n"
                f"• الاسم : {update.effective_user.first_name}\n"
                f"• المعرف : @{uname}\n"
                f"• الايدي : {uid}\n"
                f"• اللغة : {lang}\n"
                f"• عدد الاعضاء : {len(USERS)}",
            )
        except Exception:
            pass

    track_today_user(uid)
    bump_stats(is_admin(uid))

    if not await subscription_ok(update, context):
        return

    if STATE["bot_locked"] and not is_admin(uid):
        await msg.reply_text(tr("bot_locked", lang))
        return

    if is_admin(uid):
        await msg.reply_text(
            ADMIN_HEADER,
            parse_mode="Markdown",
            reply_markup=admin_menu_kb(),
        )
        return

    if STATE.get("start_message"):
        start_text = STATE["start_message"]
    else:
        start_text = tr("start", lang, channel=CHANNEL_USERNAME)

    kb = InlineKeyboardMarkup([[btn(tr("dev_btn", lang), url=DEV_LINK)]])
    await msg.reply_text(
        start_text, reply_markup=kb, disable_web_page_preview=True,
    )


# ═══════════════════════════════════════════════════════════
#  🎯 معالج الأزرار
# ═══════════════════════════════════════════════════════════

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    data = q.data or ""
    lang = get_lang(update)

    if not is_admin(uid):
        await q.answer(tr("not_admin", lang), show_alert=True)
        return
    await q.answer()

    cleanup_sessions()

    chat_id = q.message.chat_id
    sess = STATE["sessions"].setdefault(str(chat_id), {})

    if data in ("bak", "admin_panel"):
        sess.clear()
        persist()
        await q.edit_message_text(
            ADMIN_HEADER, parse_mode="Markdown",
            reply_markup=admin_menu_kb(),
        )
        return

    if data == "abcd":
        STATE["bot_locked"] = True
        persist()
        await q.edit_message_text("✅ تم قفل البوت", reply_markup=back_kb())
        return

    if data == "abcde":
        STATE["bot_locked"] = False
        persist()
        await q.edit_message_text("✅ تم فتح البوت", reply_markup=back_kb())
        return

    if data == "userd":
        shown = len(USERS) + FAKE_USERS_COUNT
        await q.edit_message_text(
            tr("users_count", lang, n=f"{shown:,}"),
            reply_markup=back_kb(),
        )
        return

    if data == "ont":
        STATE["notifications"] = True
        persist()
        await q.answer("✅ تم تفعيل الاشعارات", show_alert=True)
        return

    if data == "oft":
        STATE["notifications"] = False
        persist()
        await q.answer("⚠ تم تعطيل الاشعارات", show_alert=True)
        return

    if data == "for":
        kb = InlineKeyboardMarkup([
            [btn("اذاعه صورة", "bc_photo")],
            [btn("اذاعه رسالة", "bc_text"),
             btn("اذاعه توجيه", "bc_forward")],
            [btn("اذاعه ميديا", "bc_media"),
             btn("اذاعه انلاين", "bc_inline")],
            [btn("- الصفحه الرئيسيه", "bak")],
        ])
        await q.edit_message_text("حسناً، اختر نوع الإذاعة:", reply_markup=kb)
        return

    if data.startswith("bc_"):
        sess["action"] = "broadcast"
        sess["bc_type"] = data[3:]
        persist()
        await q.edit_message_text(
            "حسناً عزيزي\nأرسل ما تريد إذاعته للمشتركين.\n"
            "استخدم زر الإلغاء للرجوع.",
            reply_markup=cancel_kb(),
        )
        return

    if data == "channel":
        kb = InlineKeyboardMarkup([
            [btn("قناة خاصة", "sub_private")],
            [btn("قناة عامة", "sub_public")],
            [btn("- الصفحه الرئيسيه", "bak")],
        ])
        await q.edit_message_text("اختر نوع القناة:", reply_markup=kb)
        return

    if data == "sub_public":
        sess["action"] = "set_sub_username"
        persist()
        await q.edit_message_text(
            "ارسل يوزر القناة (مثال: @mychannel)\n"
            "⚠️ يجب أن يكون البوت أدمن في القناة.",
            reply_markup=cancel_kb(),
        )
        return

    if data == "sub_private":
        sess["action"] = "set_sub_link"
        sess.pop("pending_channel_id", None)
        persist()
        await q.edit_message_text(
            "الخطوة 1: ارفع البوت أدمن في القناة\n"
            "الخطوة 2: أرسل توجيه (forward) من القناة إلى هنا\n"
            "الخطوة 3: ثم أرسل رابط القناة.",
            reply_markup=cancel_kb(),
        )
        return

    if data == "off":
        if not STATE["sub_enabled"]:
            await q.answer("الاشتراك الإجباري معطل بالفعل ⚠️", show_alert=True)
        else:
            kb = InlineKeyboardMarkup([[
                btn("نعم", "sub_disable_yes"), btn("لا", "bak"),
            ]])
            await q.edit_message_text(
                "هل أنت متأكد من تعطيل الاشتراك الإجباري؟",
                reply_markup=kb,
            )
        return

    if data == "sub_disable_yes":
        STATE["sub_enabled"] = False
        STATE["sub_channel"] = ""
        STATE["sub_link"] = ""
        persist()
        await q.edit_message_text(
            "✅ تم تعطيل الاشتراك الإجباري", reply_markup=back_kb()
        )
        return

    if data == "file":
        try:
            await context.bot.send_document(
                chat_id=chat_id,
                document=InputFile(str(USERS_FILE), filename="abbas.json"),
                caption=f"نسخة لمشتركينك\nالعدد: ({len(USERS)})",
            )
        except Exception as e:
            await q.message.reply_text(f"⚠️ فشل: {e}")
        return

    if data == "up":
        sess["action"] = "upload_backup"
        persist()
        await q.edit_message_text(
            "أرسل ملف abbas.json الآن.", reply_markup=cancel_kb()
        )
        return

    if data == "pannel":
        st = STATE["stats"]
        total = st["admin_messages"] + st["user_messages"]
        today_n = len(st["today_users"])
        shown_users = len(USERS) + FAKE_USERS_COUNT
        last5 = USERS[-5:][::-1]
        last5_txt = "\n".join(
            f"▫️ {i+1}- {u}" for i, u in enumerate(last5)
        ) or "لا يوجد"
        txt = (
            f"*اهلا بك في قسم الاحصائيات 📊\n"
            f"--------------------------\n"
            f"عدد اعضاء بوتك : {shown_users:,}\n"
            f"المتفاعلين اليوم : {today_n}\n"
            f"رسائل الأدمن : {st['admin_messages']}\n"
            f"رسائل المستخدمين : {st['user_messages']}\n"
            f"مجموع الرسائل : {total}\n"
            f"--------------------------\n"
            f"اخر خمس مشتركين:\n{last5_txt}\n"
            f"--------------------------*"
        )
        await q.edit_message_text(
            txt, parse_mode="Markdown", reply_markup=back_kb()
        )
        return

    if data == "lIllabbas":
        kb = InlineKeyboardMarkup([
            [btn("- رفع ادمن .", "adl")],
            [btn("- اخر الادمنية .", "addmin")],
            [btn("- حذف الادمنيه .", "delateaddmin")],
            [btn("- الصفحه الرئيسيه", "bak")],
        ])
        await q.edit_message_text("قسم الأدمن:", reply_markup=kb)
        return

    if data == "adl":
        sess["action"] = "add_admin"
        persist()
        await q.edit_message_text(
            "قم بإرسال ايدي العضو", reply_markup=cancel_kb()
        )
        return

    if data == "addmin":
        last = STATE["admins"][-5:][::-1]
        lines = "\n".join(
            f"{i+1} - {a}" for i, a in enumerate(last)
        ) or "لا يوجد"
        await q.edit_message_text(
            f"اخر خمس ادمنيه:\n{lines}", reply_markup=back_kb()
        )
        return

    if data == "delateaddmin":
        kb = InlineKeyboardMarkup([[
            btn("نعم", "deladmins_yes"), btn("لا", "bak"),
        ]])
        await q.edit_message_text(
            "هل أنت متأكد من حذف كل الأدمنية؟", reply_markup=kb
        )
        return

    if data == "deladmins_yes":
        STATE["admins"] = []
        persist()
        await q.edit_message_text(
            "✅ تم حذف كل الأدمنية", reply_markup=back_kb()
        )
        return

    if data == "editstart":
        sess["action"] = "edit_start"
        persist()
        await q.edit_message_text(
            "قم بإرسال رسالة /start الجديدة", reply_markup=cancel_kb()
        )
        return

    if data == "xxxtentacionllllo":
        await q.answer("قسم قيد التطوير", show_alert=True)
        return


# ═══════════════════════════════════════════════════════════
#  💬 معالج الرسائل
# ═══════════════════════════════════════════════════════════

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    uid = update.effective_user.id
    chat_id = msg.chat_id
    lang = get_lang(update)

    bump_stats(is_admin(uid))
    track_today_user(uid)
    cleanup_sessions()

    if STATE["bot_locked"] and not is_admin(uid):
        await msg.reply_text(tr("bot_locked", lang))
        return

    if not await subscription_ok(update, context):
        return

    if STATE["notifications"] and not is_admin(uid):
        try:
            await context.bot.forward_message(
                chat_id=ADMIN_ID,
                from_chat_id=chat_id,
                message_id=msg.message_id,
            )
        except Exception:
            pass

    sess = STATE["sessions"].get(str(chat_id), {})
    action = sess.get("action")

    if action and is_admin(uid):
        if action == "add_admin":
            await _handle_add_admin(update, context, msg)
        elif action == "edit_start":
            await _handle_edit_start(update, context, msg)
        elif action == "set_sub_username":
            await _handle_set_sub_username(update, context, msg)
        elif action == "set_sub_link":
            await _handle_set_sub_link(update, context, msg)
        elif action == "broadcast":
            await _handle_broadcast(update, context, msg)
        elif action == "upload_backup":
            await _handle_upload_backup(update, context, msg)
        return

    text = msg.text or msg.caption or ""
    url = extract_tiktok_url(text)
    if url:
        await _handle_tiktok(update, context, url)


# ═══════════════════════════════════════════════════════════
#  🛠️ منفّذو الإجراءات
# ═══════════════════════════════════════════════════════════

async def _handle_add_admin(update, context, msg):
    text = (msg.text or "").strip()
    if not text.lstrip("-").isdigit():
        await msg.reply_text("⚠️ أرسل رقماً صحيحاً")
        return
    new_id = int(text)
    if new_id in STATE["admins"] or new_id == ADMIN_ID:
        await msg.reply_text("العضو أدمن بالفعل")
    else:
        STATE["admins"].append(new_id)
        persist()
        await msg.reply_text("✅ تم رفع العضو ادمن")
        try:
            await context.bot.send_message(new_id, "🎉 تم رفعك أدمن في البوت")
        except Exception:
            pass
    STATE["sessions"].pop(str(msg.chat_id), None)
    persist()


async def _handle_edit_start(update, context, msg):
    txt = msg.text or msg.caption
    if not txt:
        await msg.reply_text("⚠️ أرسل نصاً")
        return
    STATE["start_message"] = txt
    persist()
    STATE["sessions"].pop(str(msg.chat_id), None)
    persist()
    await msg.reply_text("✅ تم التعيين بنجاح")


async def _handle_set_sub_username(update, context, msg):
    text = (msg.text or "").strip()
    if not text.startswith("@") or len(text) < 2:
        await msg.reply_text("⚠️ أرسل يوزر بصورة صحيحة مثل: @mychannel")
        return
    try:
        me = await context.bot.get_me()
        member = await context.bot.get_chat_member(text, me.id)
        if member.status not in ("administrator", "creator"):
            await msg.reply_text("⚠️ البوت ليس أدمن في القناة. ارفعه أولاً.")
            return
    except TelegramError as e:
        await msg.reply_text(f"⚠️ تعذر التحقق: {e}")
        return
    STATE["sub_channel"] = text
    STATE["sub_link"] = f"https://t.me/{text.lstrip('@')}"
    STATE["sub_enabled"] = True
    persist()
    STATE["sessions"].pop(str(msg.chat_id), None)
    persist()
    await msg.reply_text("✅ تم تفعيل الاشتراك الإجباري")


async def _handle_set_sub_link(update, context, msg):
    sess = STATE["sessions"].setdefault(str(msg.chat_id), {})
    text = (msg.text or "").strip()

    if msg.forward_from_chat:
        sess["pending_channel_id"] = msg.forward_from_chat.id
        sess["action"] = "set_sub_link"
        persist()
        await msg.reply_text(
            f"✅ استلمت القناة: {msg.forward_from_chat.title}\n"
            f"الآن أرسل رابط القناة (مثال: https://t.me/mychannel)",
            reply_markup=cancel_kb(),
        )
        return

    channel_id = sess.get("pending_channel_id")
    if not channel_id:
        await msg.reply_text(
            "⚠️ أرسل توجيه من القناة أولاً (forward)",
            reply_markup=cancel_kb(),
        )
        return

    if not (text.startswith("http") or "t.me" in text or "telegram.me" in text):
        await msg.reply_text("⚠️ أرسل رابطاً صحيحاً")
        return

    try:
        me = await context.bot.get_me()
        member = await context.bot.get_chat_member(channel_id, me.id)
        if member.status not in ("administrator", "creator"):
            await msg.reply_text("⚠️ البوت ليس أدمن في القناة. ارفعه أولاً.")
            return
    except TelegramError as e:
        await msg.reply_text(f"⚠️ تعذر التحقق: {e}")
        return

    STATE["sub_channel"] = channel_id
    STATE["sub_link"] = text
    STATE["sub_enabled"] = True
    persist()
    sess.pop("action", None)
    sess.pop("pending_channel_id", None)
    persist()
    await msg.reply_text(
        "✅ تم تفعيل الاشتراك الإجباري بنجاح", reply_markup=back_kb()
    )


async def _handle_broadcast(update, context, msg):
    sess = STATE["sessions"].get(str(msg.chat_id), {})
    btype = sess.get("bc_type", "text")

    if btype == "forward":
        if not (msg.forward_from or msg.forward_from_chat):
            await msg.reply_text("⚠️ أرسل رسالة موجّهة (forward) للإذاعة")
            return
        await _do_broadcast_forward(context, msg)
    elif btype == "media":
        if not any([msg.photo, msg.video, msg.audio, msg.voice,
                    msg.document, msg.sticker, msg.contact]):
            await msg.reply_text("⚠️ أرسل ميديا صحيحة")
            return
        await _do_broadcast_copy(context, msg)
    elif btype == "photo":
        if not msg.photo:
            await msg.reply_text("⚠️ أرسل صورة")
            return
        await _do_broadcast_copy(context, msg)
    elif btype == "inline":
        if not (msg.forward_from or msg.forward_from_chat):
            await msg.reply_text("⚠️ أرسل رسالة موجّهة (forward)")
            return
        await _do_broadcast_forward(context, msg)
    else:
        await _do_broadcast_copy(context, msg)

    STATE["sessions"].pop(str(msg.chat_id), None)
    persist()


async def _do_broadcast_copy(context, msg):
    sent = 0
    failed = 0
    for target in list(USERS):
        if target == msg.chat_id:
            continue
        try:
            await context.bot.copy_message(
                chat_id=target,
                from_chat_id=msg.chat_id,
                message_id=msg.message_id,
            )
            sent += 1
        except TelegramError:
            failed += 1
        await asyncio.sleep(BROADCAST_DELAY)
    await msg.reply_text(
        f"✅ تم النشر إلى {sent} مشترك\n⚠️ فشل: {failed}",
        reply_markup=back_kb(),
    )


async def _do_broadcast_forward(context, msg):
    sent = 0
    failed = 0
    for target in list(USERS):
        if target == msg.chat_id:
            continue
        try:
            await context.bot.forward_message(
                chat_id=target,
                from_chat_id=msg.chat_id,
                message_id=msg.message_id,
            )
            sent += 1
        except TelegramError:
            failed += 1
        await asyncio.sleep(BROADCAST_DELAY)
    await msg.reply_text(
        f"✅ تم توجيه إلى {sent} مشترك\n⚠️ فشل: {failed}",
        reply_markup=back_kb(),
    )


async def _handle_upload_backup(update, context, msg):
    if not msg.document:
        await msg.reply_text("⚠️ أرسل ملف abbas.json")
        return
    if msg.document.file_name != "abbas.json":
        await msg.reply_text(f"⚠️ اسم الملف غير صحيح: {msg.document.file_name}")
        return
    try:
        f = await context.bot.get_file(msg.document.file_id)
        await f.download_to_drive(str(USERS_FILE))
        global USERS
        USERS = load_users()
        await msg.reply_text(
            f"✅ تم رفع الملف\nعدد المشتركين الآن: {len(USERS)}",
            reply_markup=back_kb(),
        )
    except Exception as e:
        await msg.reply_text(f"⚠️ فشل: {e}")
    STATE["sessions"].pop(str(msg.chat_id), None)
    persist()


# ═══════════════════════════════════════════════════════════
#  🎵 تيك توك — وصف الفيديو @c76xu
# ═══════════════════════════════════════════════════════════

async def _handle_tiktok(update, context, url):
    msg = update.message
    uid = update.effective_user.id
    lang = get_lang(update)

    wait_msg = await msg.reply_text(tr("fetching", lang))

    info = await fetch_tiktok(url)
    if not info:
        await wait_msg.edit_text(tr("fetch_failed", lang))
        return

    stamp = f"{uid}_{msg.message_id}_{int(time.time())}"
    tmp_video = f"dl_{stamp}.mp4"

    try:
        if await download_to_file(info["video_no_wm"], tmp_video, MAX_FILE_MB):
            try:
                with open(tmp_video, "rb") as f:
                    await context.bot.send_video(
                        chat_id=msg.chat_id,
                        video=InputFile(f, filename="video.mp4"),
                        caption=(
                            f"{tr('video_title', lang)}: {info['title']}\n"
                            f"{tr('video_id', lang)}: {info['author_id']}\n"
                            f"{tr('video_author', lang)}: {info['author_name']}\n"
                            f". — — — — — — — — — — .\n"
                            f"• Tele: {VIDEO_CREDIT}"
                        ),
                    )
            except TelegramError as e:
                logger.error(f"send video: {e}")
                await msg.reply_text(tr("send_failed", lang, err=str(e)))
        else:
            await msg.reply_text(tr("download_failed", lang))
    finally:
        try:
            if os.path.exists(tmp_video):
                os.remove(tmp_video)
                logger.info(f"🗑️ تم حذف {tmp_video}")
        except Exception as e:
            logger.error(f"remove tmp: {e}")

    try:
        await wait_msg.delete()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
#  ⚠️ معالج الأخطاء
# ═══════════════════════════════════════════════════════════

async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Unhandled error", exc_info=context.error)
    if isinstance(update, Update) and update.effective_user:
        try:
            await context.bot.send_message(
                ADMIN_ID,
                f"⚠️ خطأ في البوت:\n"
                f"User: {update.effective_user.id}\n"
                f"Error: {context.error}",
            )
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
#  🚀 MAIN
# ═══════════════════════════════════════════════════════════

def main():
    print("=" * 50)
    print(f"🔍 BOT_TOKEN: {'✅ موجود' if BOT_TOKEN else '❌ مفقود'}")
    print(f"🔍 ADMIN_ID: {ADMIN_ID}")
    print(f"🔍 CHANNEL: {CHANNEL_USERNAME}")
    print(f"🔍 VIDEO_CREDIT: {VIDEO_CREDIT}")
    print(f"🔍 Languages: {', '.join(LANGUAGES.keys())}")
    print(f"🔍 Fake users: {FAKE_USERS_COUNT:,}")
    print("=" * 50)

    if not BOT_TOKEN or ":" not in BOT_TOKEN:
        print("❌ التوكن غير صالح")
        return
    if not ADMIN_ID:
        print("❌ ADMIN_ID غير صالح")
        return

    print("🚀 تشغيل البوت...")
    try:
        app = Application.builder().token(BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CallbackQueryHandler(on_callback))
        app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, on_message))
        app.add_error_handler(on_error)

        logger.info("🚀 البوت يعمل...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print("=" * 50)
        print(f"❌ خطأ فادح: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 50)


if __name__ == "__main__":
    main()
