# ═══════════════════════════════════════════════════════════
#  📦 المكتبات (أولاً)
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
#  ⚙️ الإعدادات — عدّل هنا فقط
# ═══════════════════════════════════════════════════════════

BOT_TOKEN = "6198804155:AAF5Zj-co6guQ6s2bW5hMTvFga8CFRi0WqA" 
ADMIN_ID  = 5952132218               # ← ايدي المطور (رقم فقط)

DEV_USERNAME = "@c76me"
DEV_LINK     = "https://t.me/c76xu"

# ═══════════════════════════════════════════════════════════
#  🔧 ثوابت داخلية — لا تعدّلها
# ═══════════════════════════════════════════════════════════

STATE_FILE  = "state.json"
USERS_FILE  = "abbas.json"
MAX_FILE_MB = 48
BROADCAST_DELAY = 0.05
MAX_SESSIONS = 500
KEEP_SESSIONS = 100

DEFAULT_START = """• اهلا بك اخي في بوت تحميل من تيك توك 🐿️.
• فقط ارسل الرابط وسيتم ارسال المقطع بدون علامةه مائيةه 🤍.
. — — — — — — — — — — .
• Tele : @OoOoO2oO | @T3bsBoT ."""

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
#  🌐 الحالة العامة (بعد تحميل المكتبات والدوال)
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
#  🎛️ أزرار مساعدة
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
#  🔒 فحص الاشتراك الإجباري
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

    is_new = add_user(uid)
    if is_new and not is_admin(uid):
        try:
            await context.bot.send_message(
                ADMIN_ID,
                f"٭ تم دخول شخص جديد الى البوت 👾\n\n"
                f"• الاسم : {update.effective_user.first_name}\n"
                f"• المعرف : @{uname}\n"
                f"• الايدي : {uid}\n"
                f"• عدد الاعضاء : {len(USERS)}",
            )
        except Exception:
            pass

    track_today_user(uid)
    bump_stats(is_admin(uid))

    if not await subscription_ok(update, context):
        return

    if STATE["bot_locked"] and not is_admin(uid):
        await msg.reply_text("عذرا البوت يخضع للتحديث الان")
        return

    if is_admin(uid):
        await msg.reply_text(
            ADMIN_HEADER,
            parse_mode="Markdown",
            reply_markup=admin_menu_kb(),
        )
        return

    start_text = STATE.get("start_message") or DEFAULT_START
    kb = InlineKeyboardMarkup([[btn("• المطور .", url=DEV_LINK)]])
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

    if not is_admin(uid):
        await q.answer("هذا الأمر للمشرفين فقط ⚠️", show_alert=True)
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
        await q.edit_message_text(
            f"👥 عدد الاعضاء: {len(USERS)}", reply_markup=back_kb()
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
        last5 = USERS[-5:][::-1]
        last5_txt = "\n".join(
            f"▫️ {i+1}- {u}" for i, u in enumerate(last5)
        ) or "لا يوجد"
        txt = (
            f"*اهلا بك في قسم الاحصائيات 📊\n"
            f"--------------------------\n"
            f"عدد اعضاء بوتك : {len(USERS)}\n"
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

    bump_stats(is_admin(uid))
    track_today_user(uid)
    cleanup_sessions()

    if STATE["bot_locked"] and not is_admin(uid):
        await msg.reply_text("عذرا البوت يخضع للتحديث الان")
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


async def _handle_tiktok(update, context, url):
    msg = update.message
    uid = update.effective_user.id

    wait_msg = await msg.reply_text("⏳ جاري جلب الفيديو...")

    info = await fetch_tiktok(url)
    if not info:
        await wait_msg.edit_text("❌ فشل جلب الفيديو. جرب رابطاً آخر.")
        return

    stamp = f"{uid}_{msg.message_id}_{int(time.time())}"
    tmp_v_no_wm = f"dl_{stamp}_nowm.mp4"
    tmp_v_wm = f"dl_{stamp}_wm.mp4"
    tmp_audio = f"dl_{stamp}.mp3"

    try:
        if await download_to_file(info["video_no_wm"], tmp_v_no_wm, MAX_FILE_MB):
            try:
                with open(tmp_v_no_wm, "rb") as f:
                    await context.bot.send_video(
                        chat_id=msg.chat_id,
                        video=InputFile(f, filename="video.mp4"),
                        caption=(
                            f"العنوان: {info['title']}\n"
                            f"المعرف: {info['author_id']}\n"
                            f"الاسم: {info['author_name']}\n"
                            f"النوع: بدون علامة\n"
                            f". — — — — — — — — — — .\n"
                            f"• Tele: @OoOoO2oO | @T3bsBoT ."
                        ),
                    )
            except TelegramError as e:
                logger.error(f"send no-wm: {e}")
        else:
            await msg.reply_text(
                "⚠️ تعذر تحميل النسخة بدون علامة (حجم كبير أو رابط معطوب)"
            )

        if info["video_wm"] and info["video_wm"] != info["video_no_wm"]:
            if await download_to_file(info["video_wm"], tmp_v_wm, MAX_FILE_MB):
                try:
                    with open(tmp_v_wm, "rb") as f:
                        await context.bot.send_video(
                            chat_id=msg.chat_id,
                            video=InputFile(f, filename="video_wm.mp4"),
                            caption=(
                                f"العنوان: {info['title']}\n"
                                f"المعرف: {info['author_id']}\n"
                                f"الاسم: {info['author_name']}\n"
                                f"النوع: مع علامة\n"
                                f". — — — — — — — — — — .\n"
                                f"• Tele: @OoOoO2oO | @T3bsBoT ."
                            ),
                        )
                except TelegramError as e:
                    logger.error(f"send wm: {e}")

        if info["audio"]:
            if await download_to_file(info["audio"], tmp_audio, MAX_FILE_MB):
                try:
                    with open(tmp_audio, "rb") as f:
                        await context.bot.send_audio(
                            chat_id=msg.chat_id,
                            audio=InputFile(f, filename="audio.mp3"),
                            caption=(
                                f"العنوان: {info['title']}\n"
                                f"الاسم: {info['author_name']}\n"
                                f". — — — — — — — — — — .\n"
                                f"• Tele: @OoOoO2oO | @T3bsBoT ."
                            ),
                        )
                except TelegramError as e:
                    logger.error(f"send audio: {e}")
    finally:
        for p in (tmp_v_no_wm, tmp_v_wm, tmp_audio):
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

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
    if not BOT_TOKEN or ":" not in BOT_TOKEN:
        print("❌ ضع التوكن في BOT_TOKEN (تحت المكتبات)")
        return
    if not ADMIN_ID:
        print("❌ ضع معرفك في ADMIN_ID (تحت المكتبات)")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, on_message))
    app.add_error_handler(on_error)

    logger.info("🚀 البوت يعمل...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
