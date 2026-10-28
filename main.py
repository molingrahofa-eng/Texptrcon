# ═══════════════════════════════════════════════════════════════
#  بوت تنزيل 100 فيديو + حذف فوري
#  لا يخزن سوى tweet_id في JSON صغير
# ═══════════════════════════════════════════════════════════════

import asyncio
import hashlib
import json
import os
import re
import sys
import time
import uuid
from datetime import date
from typing import Optional
from urllib.parse import urlsplit

import httpx
import feedparser
from loguru import logger as _logger
from telegram import (
    BotCommand, InlineKeyboardButton, InlineKeyboardMarkup,
    InlineQueryResultArticle, InlineQueryResultCachedPhoto,
    InlineQueryResultCachedVideo, InputFile,
    InputTextMessageContent, Update,
)
from telegram.constants import ChatAction, ParseMode
from telegram.error import TelegramError
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler,
    InlineQueryHandler, MessageHandler, filters,
)

# ═══════════════════════════════════════════════════════════════
#  الإعدادات
# ═══════════════════════════════════════════════════════════════

BOT_TOKEN = "6198804155:AAF5Zj-co6guQ6s2bW5hMTvFga8CFRi0WqA"
DEVELOPER_ID = 5952132218
DEVELOPER_NAME = "Ahmed"
DEVELOPER_CONTACT = "@YourUsername"

RSSHUB_BASE = "https://your-rsshub.up.railway.app"

USE_LOCAL_API = False
LOCAL_API_URL = "http://localhost:8081/bot"
LOCAL_API_FILE_URL = "http://localhost:8081/file/bot"

if USE_LOCAL_API:
    MAX_FILE_SIZE = 2000 * 1024 * 1024
else:
    MAX_FILE_SIZE = 50 * 1024 * 1024

USER_DAILY_LIMIT = 10
ADMIN_DAILY_LIMIT = 99999

DOWNLOAD_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 📄 ملف JSON صغير لتتبع tweet_id فقط
TRACK_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "tracked_ids.json")

AUTO_DELETE_SECONDS = 60
BATCH_SIZE = 100
UPLOAD_READ_TIMEOUT = 1800
UPLOAD_WRITE_TIMEOUT = 1800
DOWNLOAD_TIMEOUT = 900

BOT_USERNAME = ""
BLANK = "\u2800"

# ═══════════════════════════════════════════════════════════════
#  السجل
# ═══════════════════════════════════════════════════════════════

_logger.remove()
_logger.add(sys.stderr, level="INFO")
_logger.add("bot.log", rotation="10 MB",
            retention="3 days", level="DEBUG")
logger = _logger.bind(service="twitter_bot")

background_tasks: set = set()


# ═══════════════════════════════════════════════════════════════
#  📄 ملف JSON صغير (بدل قاعدة بيانات)
# ═══════════════════════════════════════════════════════════════

def load_tracked():
    """يقرأ tweet_ids المحفوظة (ملف صغير جداً)."""
    if not os.path.exists(TRACK_FILE):
        return {}
    try:
        with open(TRACK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_tracked(data):
    """يحفظ tweet_ids (ملف < 10 KB)."""
    try:
        with open(TRACK_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        logger.warning("save_tracked: {}", e)


def is_processed(tweet_id):
    data = load_tracked()
    return tweet_id in data


def mark_processed(tweet_id):
    data = load_tracked()
    data[tweet_id] = int(time.time())
    # الاحتفاظ بآخر 5000 فقط لتجنب كبر الملف
    if len(data) > 5000:
        sorted_items = sorted(
            data.items(), key=lambda x: x[1], reverse=True)
        data = dict(sorted_items[:5000])
    save_tracked(data)


# ═══════════════════════════════════════════════════════════════
#  أدوات
# ═══════════════════════════════════════════════════════════════

TWEET_URL_RE = re.compile(
    r"(?:twitter\.com|x\.com|fxtwitter\.com|"
    r"vxtwitter\.com)/[^/\s]+/status(?:es)?/(\d+)",
    re.IGNORECASE)
URL_RE = re.compile(r"https?://\S+")


def extract_tweet_id(url):
    m = TWEET_URL_RE.search(url or "")
    return m.group(1) if m else None


def normalize_kind(t):
    if t in {"image", "photo"}: return "photo"
    if t in {"video", "gif"}: return "video"
    return None


def extract_media_items(tweet_media):
    items = []
    for it in tweet_media.get("media_extended") or []:
        if not isinstance(it, dict):
            continue
        url = it.get("url")
        kind = normalize_kind(it.get("type"))
        if url and kind:
            items.append({"url": url, "type": kind})
    return items


def build_media_id(url):
    return hashlib.md5(url.encode()).hexdigest()[:16]


def build_caption(post_url):
    if BOT_USERNAME:
        bot_link = (f'<a href="https://t.me/{BOT_USERNAME}">'
                    f"@{BOT_USERNAME}</a>")
        return (f"🐦 بوت التحميل {bot_link}\n"
                f'🔗 <a href="{post_url}">المصدر</a>')
    return (f"🐦 بوت التحميل\n"
            f'🔗 <a href="{post_url}">المصدر</a>')


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024: return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ═══════════════════════════════════════════════════════════════
#  جلب التغريدة
# ═══════════════════════════════════════════════════════════════

async def fetch_tweet_media_fx(tweet_id):
    headers = {"User-Agent": "Mozilla/5.0",
               "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(
            f"https://api.fxtwitter.com/status/{tweet_id}",
            headers=headers)
        r.raise_for_status()
        data = r.json()
    tweet = data.get("tweet") or {}
    media = tweet.get("media") or {}
    me = []
    for p in media.get("photos") or []:
        if p.get("url"):
            me.append({"type": "photo", "url": p["url"]})
    for v in media.get("videos") or []:
        if v.get("url"):
            me.append({"type": "video", "url": v["url"]})
    return {
        "tweetURL": tweet.get("url")
        or f"https://x.com/i/status/{tweet_id}",
        "media_extended": me,
    }


async def fetch_tweet_media_vx(tweet_id):
    headers = {"User-Agent": "Mozilla/5.0",
               "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(
            f"https://api.vxtwitter.com/status/{tweet_id}",
            headers=headers)
        r.raise_for_status()
        data = r.json()
    me = []
    for m in data.get("media_extended") or []:
        t = m.get("type")
        if t == "image":
            me.append({"type": "photo", "url": m.get("url")})
        elif t == "video":
            me.append({"type": "video", "url": m.get("url")})
    return {
        "tweetURL": data.get("tweetURL")
        or f"https://x.com/i/status/{tweet_id}",
        "media_extended": me,
    }


async def fetch_tweet_media(tweet_id):
    for name, fn in [
        ("fxtwitter", fetch_tweet_media_fx),
        ("vxtwitter", fetch_tweet_media_vx),
    ]:
        try:
            return await fn(tweet_id)
        except Exception:
            continue
    raise RuntimeError("فشل جلب التغريدة")


# ═══════════════════════════════════════════════════════════════
#  RSSHub - جلب آخر 100 تغريدة
# ═══════════════════════════════════════════════════════════════

async def fetch_100_tweet_ids(username, limit=100):
    url = (f"{RSSHUB_BASE}/twitter/user/{username}"
           f"?limit={limit}")
    headers = {"User-Agent": "Mozilla/5.0"}
    async with httpx.AsyncClient(
            timeout=30, follow_redirects=True) as client:
        r = await client.get(url, headers=headers)
        if r.status_code != 200:
            raise RuntimeError(
                f"RSSHub {r.status_code}")
        feed = feedparser.parse(r.text)

    ids = []
    for entry in feed.entries:
        link = entry.get("link", "")
        m = TWEET_URL_RE.search(link)
        if m:
            ids.append(m.group(1))
    return ids[:limit]


# ═══════════════════════════════════════════════════════════════
#  التنزيل
# ═══════════════════════════════════════════════════════════════

class DownloadTooLargeError(Exception):
    pass


class Downloader:
    def __init__(self, output_dir, max_size):
        self.output_dir = output_dir
        self.max_size = max_size

    async def download(self, url, filename):
        """ينزّل ملفاً مؤقتاً - يجب حذفه بعد الإرسال."""
        full = os.path.join(self.output_dir, filename)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        headers = {"User-Agent": "Mozilla/5.0",
                   "Referer": "https://x.com/"}
        timeout = httpx.Timeout(DOWNLOAD_TIMEOUT, connect=30)
        async with httpx.AsyncClient(
                timeout=timeout, follow_redirects=True,
                headers=headers) as client:
            async with client.stream("GET", url) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                if total and total > self.max_size:
                    raise DownloadTooLargeError(
                        f"{human_size(total)} > "
                        f"{human_size(self.max_size)}")
                downloaded = 0
                with open(full, "wb") as f:
                    async for chunk in r.aiter_bytes(256 * 1024):
                        downloaded += len(chunk)
                        if downloaded > self.max_size:
                            f.close()
                            os.remove(full)
                            raise DownloadTooLargeError("تجاوز")
                        f.write(chunk)
        return full


downloader = Downloader(DOWNLOAD_DIR, MAX_FILE_SIZE)


# ═══════════════════════════════════════════════════════════════
#  إرسال الوسائط
# ═══════════════════════════════════════════════════════════════

async def send_video_file(chat_id, context, path,
                          caption=None, reply_markup=None):
    f = open(path, "rb")
    try:
        return await context.bot.send_video(
            chat_id=chat_id,
            video=InputFile(f, filename=os.path.basename(path)),
            caption=caption,
            parse_mode=ParseMode.HTML,
            supports_streaming=True,
            reply_markup=reply_markup,
            read_timeout=UPLOAD_READ_TIMEOUT,
            write_timeout=UPLOAD_WRITE_TIMEOUT,
            connect_timeout=60)
    finally:
        f.close()


async def send_single_photo(chat_id, context, path,
                            caption=None, reply_markup=None):
    f = open(path, "rb")
    try:
        return await context.bot.send_photo(
            chat_id=chat_id,
            photo=InputFile(f, filename=os.path.basename(path)),
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            read_timeout=UPLOAD_READ_TIMEOUT,
            write_timeout=UPLOAD_WRITE_TIMEOUT,
            connect_timeout=60)
    finally:
        f.close()


# ═══════════════════════════════════════════════════════════════
#  ⭐ الميزة الجديدة: تنزيل 100 فيديو + حذف فوري
# ═══════════════════════════════════════════════════════════════

async def process_batch_100(update, context, username):
    """
    يجلب آخر 100 تغريدة، ينزّل الفيديوهات واحداً واحداً،
    يرسلها، ثم يحذف الملف فوراً.
    """
    message = update.effective_message
    user = update.effective_user

    if user.id != DEVELOPER_ID:
        await message.reply_text(
            "⛔ هذه الميزة للمشرف فقط.")
        return

    status = await message.reply_text(
        f"🔍 <b>جاري جلب آخر {BATCH_SIZE} تغريدة "
        f"من @{username}...</b>",
        parse_mode=ParseMode.HTML)

    try:
        all_ids = await fetch_100_tweet_ids(
            username, BATCH_SIZE)
    except Exception as e:
        try:
            await status.edit_text(
                f"❌ <b>فشل جلب التغريدات</b>\n\n"
                f"<code>{str(e)[:300]}</code>\n\n"
                "تأكد من:\n"
                "• رابط RSSHub في RSSHUB_BASE\n"
                "• الحساب عام",
                parse_mode=ParseMode.HTML)
        except TelegramError: pass
        return

    if not all_ids:
        try:
            await status.edit_text(
                f"⚠️ لا توجد تغريدات لـ @{username}")
        except TelegramError: pass
        return

    total = len(all_ids)
    logger.info("🎬 @{}: {} tweets to process",
                username, total)

    # تصفية المعالجة سابقاً
    new_ids = [tid for tid in all_ids
               if not is_processed(tid)]

    if not new_ids:
        try:
            await status.edit_text(
                f"✅ <b>كل التغريدات معالجة مسبقاً</b>\n\n"
                f"📊 العدد: {total}\n"
                f"💡 أرسل /reset لتجاهل السجل",
                parse_mode=ParseMode.HTML)
        except TelegramError: pass
        return

    await status.edit_text(
        f"📥 <b>جاري التنزيل...</b>\n\n"
        f"📊 العدد: <b>{len(new_ids)}/{total}</b>\n"
        f"🗑️ سيُحذف كل ملف بعد الإرسال\n"
        f"⏳ <b>0/{len(new_ids)}</b>",
        parse_mode=ParseMode.HTML)

    downloaded_count = 0
    failed_count = 0
    skipped_count = 0

    for idx, tweet_id in enumerate(new_ids, 1):
        # تحديث الحالة كل 3 تغريدات
        if idx % 3 == 0 or idx == len(new_ids):
            try:
                pct = int((idx / len(new_ids)) * 100)
                bar = "▓" * (pct // 10) + "░" * (10 - pct // 10)
                await status.edit_text(
                    f"📥 <b>جاري التنزيل...</b>\n\n"
                    f"{bar} {pct}%\n\n"
                    f"⏳ <b>{idx}/{len(new_ids)}</b>\n"
                    f"✅ نُزّل: {downloaded_count}\n"
                    f"⏭️ تخطي: {skipped_count}\n"
                    f"❌ فشل: {failed_count}",
                    parse_mode=ParseMode.HTML)
            except TelegramError: pass

        # جلب بيانات التغريدة
        try:
            tweet_media = await fetch_tweet_media(tweet_id)
        except Exception as e:
            logger.debug("Fetch {}: {}", tweet_id, e)
            failed_count += 1
            continue

        items = extract_media_items(tweet_media)
        if not items:
            skipped_count += 1
            mark_processed(tweet_id)
            continue

        post_url = tweet_media.get(
            "tweetURL",
            f"https://x.com/{username}/status/{tweet_id}")
        caption = build_caption(post_url)

        # تنزيل + إرسال + حذف فوري
        tweet_sent = 0
        for m_idx, item in enumerate(items):
            ext = os.path.splitext(
                urlsplit(item["url"]).path)[1]
            if not ext:
                ext = ".jpg" if item["type"] == "photo" else ".mp4"
            request_id = uuid.uuid4().hex[:8]
            fname = f"batch_{tweet_id}_{m_idx}_{request_id}{ext}"

            temp_path = None
            try:
                # ═══ 1) تنزيل مؤقت ═══
                temp_path = await downloader.download(
                    item["url"], fname)
                size = os.path.getsize(temp_path)
                if size > MAX_FILE_SIZE:
                    continue

                # ═══ 2) إرسال ═══
                if item["type"] == "video":
                    await context.bot.send_chat_action(
                        chat_id=message.chat_id,
                        action=ChatAction.UPLOAD_VIDEO)
                    await send_video_file(
                        message.chat_id, context,
                        temp_path, caption=caption)
                else:
                    await context.bot.send_chat_action(
                        chat_id=message.chat_id,
                        action=ChatAction.UPLOAD_PHOTO)
                    await send_single_photo(
                        message.chat_id, context,
                        temp_path, caption=caption)

                tweet_sent += 1
                caption = None  # الكابشن للأول فقط

            except DownloadTooLargeError:
                logger.debug("Too large: {}", tweet_id)
            except TelegramError as e:
                logger.warning("Send {}: {}", tweet_id, e)
            except Exception as e:
                logger.debug("Download {}: {}", tweet_id, e)
            finally:
                # ═══ 3) 🗑️ حذف فوري (دائماً) ═══
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                        logger.debug("Deleted: {}", temp_path)
                    except OSError as e:
                        logger.warning("Delete failed: {}", e)

        if tweet_sent > 0:
            downloaded_count += 1
            mark_processed(tweet_id)

        # تأخير بسيط لتجنب Rate Limit
        await asyncio.sleep(0.5)

    # ═══ رسالة النهاية ═══
    final_text = (
        f"✅ <b>اكتمل التنزيل</b>\n\n"
        f"📊 <b>النتائج:</b>\n"
        f"• ✅ تغريدات نُزّلت: <b>{downloaded_count}</b>\n"
        f"• ⏭️ تخطي: <b>{skipped_count}</b>\n"
        f"• ❌ فشل: <b>{failed_count}</b>\n"
        f"• 📦 الإجمالي: <b>{len(new_ids)}</b>\n\n"
        f"🗑️ <b>تم حذف جميع الملفات المؤقتة</b>\n"
        f"💾 لم يبقَ سوى tweet_ids في "
        f"<code>tracked_ids.json</code>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🏠  القائمة الرئيسية",
            callback_data="menu:main")]])
    try:
        await status.edit_text(
            final_text, parse_mode=ParseMode.HTML,
            reply_markup=kb)
    except TelegramError: pass


# ═══════════════════════════════════════════════════════════════
#  الاشتراك الإجباري (مبسط)
# ═══════════════════════════════════════════════════════════════

async def require_subscription(update, context):
    """تحقق مبسط - بدون قنوات = مسموح."""
    return True


def check_daily_limit(user_id):
    if user_id == DEVELOPER_ID:
        return True, 0, ADMIN_DAILY_LIMIT
    return True, 0, USER_DAILY_LIMIT


# ═══════════════════════════════════════════════════════════════
#  لوحات المفاتيح
# ═══════════════════════════════════════════════════════════════

def media_actions_keyboard(media_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "📤 مشاركة",
            switch_inline_query=f"media:{media_id}")]])


def main_menu_keyboard(is_admin=False):
    rows = [
        [InlineKeyboardButton(
            "📥  تنزيل تغريدة واحدة",
            callback_data="menu:download")],
        [InlineKeyboardButton(
            "🎬  تنزيل 100 فيديو",
            callback_data="menu:batch100")],
        [InlineKeyboardButton(
            "📊  إحصائياتي",
            callback_data="menu:stats")],
        [InlineKeyboardButton(
            "ℹ️  كيف يعمل البوت؟",
            callback_data="menu:howto")],
    ]
    return InlineKeyboardMarkup(rows)


def back_button(callback="menu:main",
                text="🔙  رجوع"):
    return InlineKeyboardButton(text, callback_data=callback)


# ═══════════════════════════════════════════════════════════════
#  النصوص
# ═══════════════════════════════════════════════════════════════

def main_menu_text(user):
    tracked = load_tracked()
    text = (
        "╭──────────────────╮\n"
        "     🐦 <b>TWITTER BOT</b>\n"
        "╰──────────────────╯\n\n"
        f"👤 أهلاً <b>{user.first_name or 'صديقي'}</b>!\n\n"
        f"📊 في السجل: <b>{len(tracked)}</b> تغريدة\n"
        f"📦 حد الملف: <b>{human_size(MAX_FILE_SIZE)}</b>\n\n"
        "اختر من القائمة 👇")
    return text


HOWTO_TEXT = (
    "╭──────────────────╮\n"
    "     📖 <b>كيف يعمل البوت</b>\n"
    "╰──────────────────╯\n\n"
    "<b>📥 تنزيل تغريدة واحدة:</b>\n"
    "أرسل رابط التغريدة مباشرة\n\n"
    "<b>🎬 تنزيل 100 فيديو:</b>\n"
    "أرسل <code>/fetch100 @username</code>\n\n"
    "━━━━━━━━━━━━━━━━━\n"
    "💡 <b>ملاحظات:</b>\n"
    "• يتم حذف كل ملف بعد الإرسال فوراً\n"
    "• يُحفظ tweet_id فقط في JSON\n"
    "• لا توجد قاعدة بيانات\n"
    "• لا توجد ملفات دائمة"
)


# ═══════════════════════════════════════════════════════════════
#  تنزيل تغريدة واحدة
# ═══════════════════════════════════════════════════════════════

async def process_single_tweet(update, context, url, tweet_id):
    message = update.effective_message

    status = await message.reply_text(
        "⏳ <b>جاري المعالجة...</b>",
        parse_mode=ParseMode.HTML)

    try:
        tweet_media = await fetch_tweet_media(tweet_id)
    except Exception as e:
        try:
            await status.edit_text(
                f"❌ <code>{str(e)[:300]}</code>",
                parse_mode=ParseMode.HTML)
        except TelegramError: pass
        return False

    items = extract_media_items(tweet_media)
    if not items:
        try:
            await status.edit_text("⚠️ لا وسائط.")
        except TelegramError: pass
        return False

    post_url = tweet_media.get("tweetURL", url)
    caption_text = build_caption(post_url)
    request_id = uuid.uuid4().hex[:8]

    for idx, item in enumerate(items):
        ext = os.path.splitext(
            urlsplit(item["url"]).path)[1]
        if not ext:
            ext = ".jpg" if item["type"] == "photo" else ".mp4"
        fname = f"single_{tweet_id}_{idx}_{request_id}{ext}"
        temp_path = None

        try:
            temp_path = await downloader.download(
                item["url"], fname)
            if os.path.getsize(temp_path) > MAX_FILE_SIZE:
                continue

            media_id = build_media_id(item["url"])
            if item["type"] == "video":
                await send_video_file(
                    message.chat_id, context, temp_path,
                    caption=caption_text,
                    reply_markup=media_actions_keyboard(media_id))
            else:
                await send_single_photo(
                    message.chat_id, context, temp_path,
                    caption=caption_text,
                    reply_markup=media_actions_keyboard(media_id))
            caption_text = None

        except Exception as e:
            logger.exception("Send: {}", e)
        finally:
            # 🗑️ حذف فوري
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError: pass

    mark_processed(tweet_id)

    try:
        await status.delete()
    except TelegramError: pass
    return True


# ═══════════════════════════════════════════════════════════════
#  شاشات
# ═══════════════════════════════════════════════════════════════

async def show_main_menu(update, context, edit=True):
    user = update.effective_user
    text = main_menu_text(user)
    kb = main_menu_keyboard()
    if edit and update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text, parse_mode=ParseMode.HTML,
                reply_markup=kb)
            return
        except TelegramError: pass
    if update.callback_query:
        await update.callback_query.message.reply_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await update.message.reply_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def show_howto(update, context):
    kb = InlineKeyboardMarkup([[back_button()]])
    try:
        await update.callback_query.edit_message_text(
            HOWTO_TEXT, parse_mode=ParseMode.HTML,
            reply_markup=kb)
    except TelegramError:
        await update.callback_query.message.reply_text(
            HOWTO_TEXT, parse_mode=ParseMode.HTML,
            reply_markup=kb)


async def show_batch100_prompt(update, context):
    text = (
        "╭──────────────────╮\n"
        "     🎬 <b>تنزيل 100 فيديو</b>\n"
        "╰──────────────────╯\n\n"
        "📎 <b>أرسل:</b>\n"
        "<code>/fetch100 @username</code>\n\n"
        "📌 مثال:\n"
        "<code>/fetch100 @elonmusk</code>\n\n"
        "━━━━━━━━━━━━━━━━━\n"
        "💡 <b>ملاحظات:</b>\n"
        f"• يجلب آخر <b>{BATCH_SIZE}</b> تغريدة\n"
        "• ينزّل الفيديوهات/الصور واحداً واحداً\n"
        "• 🗑️ يحذف كل ملف فور إرساله\n"
        "• يُحفظ tweet_id فقط (JSON)\n"
        "• ⏱️ قد يستغرق 10-30 دقيقة")
    kb = InlineKeyboardMarkup([[back_button()]])
    try:
        await update.callback_query.edit_message_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except TelegramError:
        await update.callback_query.message.reply_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb)


# ═══════════════════════════════════════════════════════════════
#  الأوامر
# ═══════════════════════════════════════════════════════════════

async def start_command(update, context):
    user = update.effective_user
    text = (
        "╭──────────────────────────╮\n"
        "   🚀 <b>مرحباً بك</b>\n"
        "╰──────────────────────────╯\n\n"
        "🔹 <b>تغريدة واحدة:</b> أرسل الرابط\n"
        "🔹 <b>100 فيديو:</b> /fetch100 @username\n\n"
        f"📦 الحد: <b>{human_size(MAX_FILE_SIZE)}</b>")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🚀  ابدأ", callback_data="menu:main")]])
    await update.message.reply_text(
        text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def menu_command(update, context):
    await show_main_menu(update, context, edit=False)


async def fetch100_command(update, context):
    """أمر /fetch100 @username"""
    if not context.args:
        await update.message.reply_text(
            "الاستخدام: <code>/fetch100 @username</code>",
            parse_mode=ParseMode.HTML)
        return

    username = context.args[0].lstrip("@")
    await process_batch_100(update, context, username)


async def reset_command(update, context):
    """يحذف ملف tracked_ids.json"""
    if update.effective_user.id != DEVELOPER_ID:
        return
    if os.path.exists(TRACK_FILE):
        os.remove(TRACK_FILE)
    await update.message.reply_text(
        "✅ <b>تم مسح سجل التغريدات</b>\n\n"
        "الآن يمكنك إعادة تنزيل كل شيء.",
        parse_mode=ParseMode.HTML)


async def stats_command(update, context):
    tracked = load_tracked()
    downloads_dir = DOWNLOAD_DIR
    files_count = 0
    total_size = 0
    if os.path.exists(downloads_dir):
        for f in os.listdir(downloads_dir):
            fp = os.path.join(downloads_dir, f)
            if os.path.isfile(fp):
                files_count += 1
                total_size += os.path.getsize(fp)

    text = (
        "📊 <b>إحصائيات</b>\n\n"
        f"📄 tweet_ids في JSON: <b>{len(tracked)}</b>\n"
        f"📁 ملفات مؤقتة: <b>{files_count}</b>\n"
        f"💾 حجم الملفات: <b>{human_size(total_size)}</b>\n\n"
        "💡 الملفات المؤقتة تُحذف تلقائياً بعد كل إرسال.")
    await update.message.reply_text(
        text, parse_mode=ParseMode.HTML)


# ═══════════════════════════════════════════════════════════════
#  معالج الأزرار
# ═══════════════════════════════════════════════════════════════

async def callback_handler(update, context):
    query = update.callback_query
    data = query.data or ""
    try: await query.answer()
    except TelegramError: pass

    if data == "menu:main":
        await show_main_menu(update, context, edit=True)
        return
    if data == "menu:batch100":
        await show_batch100_prompt(update, context)
        return
    if data == "menu:howto":
        await show_howto(update, context)
        return
    if data == "menu:download":
        text = ("📥 <b>تنزيل تغريدة</b>\n\n"
                "أرسل رابط التغريدة مباشرة.")
        kb = InlineKeyboardMarkup([[back_button()]])
        try:
            await query.edit_message_text(
                text, parse_mode=ParseMode.HTML,
                reply_markup=kb)
        except TelegramError: pass
        return


# ═══════════════════════════════════════════════════════════════
#  معالج الرسائل
# ═══════════════════════════════════════════════════════════════

async def handle_message(update, context):
    message = update.effective_message
    user = update.effective_user
    if not message or not user: return

    if not message.text: return
    text = message.text.strip()

    match = URL_RE.search(text)
    if not match:
        await message.reply_text(
            "❓ أرسل <b>رابط تغريدة</b> أو "
            "<code>/fetch100 @username</code>",
            parse_mode=ParseMode.HTML)
        return

    url = match.group(0)
    tweet_id = extract_tweet_id(url)
    if not tweet_id:
        await message.reply_text("❌ رابط غير صالح.")
        return

    try:
        await process_single_tweet(
            update, context, url, tweet_id)
    except Exception as e:
        logger.exception("Error: {}", e)
        await message.reply_text(f"❌ خطأ: {str(e)[:200]}")


# ═══════════════════════════════════════════════════════════════
#  post_init + main
# ═══════════════════════════════════════════════════════════════

async def error_handler(update, context):
    logger.error("Error: {}", context.error)
    try:
        await context.bot.send_message(
            DEVELOPER_ID,
            f"⚠️ خطأ:\n"
            f"<code>{str(context.error)[:400]}</code>",
            parse_mode=ParseMode.HTML)
    except Exception: pass


async def post_init(app):
    global BOT_USERNAME
    try:
        me = await app.bot.get_me()
        BOT_USERNAME = me.username or ""
        logger.info("Bot: @{}", BOT_USERNAME)
        print(f"✅ Bot: @{BOT_USERNAME}")
    except Exception as e:
        logger.warning("Bot username: {}", e)

    await app.bot.set_my_commands([
        BotCommand("start", "🚀 بدء البوت"),
        BotCommand("menu", "🏠 القائمة"),
        BotCommand("fetch100", "🎬 تنزيل 100 فيديو"),
        BotCommand("stats", "📊 إحصائيات"),
        BotCommand("reset", "🔄 مسح السجل"),
    ])


def main():
    if (not BOT_TOKEN
            or BOT_TOKEN == "ضع_توكن_البوت_هنا"):
        print("⚠️ ضع توكن البوت")
        sys.exit(1)
    if "your-rsshub" in RSSHUB_BASE:
        print("⚠️ ضع رابط RSSHub في RSSHUB_BASE")
        sys.exit(1)

    builder = Application.builder().token(BOT_TOKEN)
    if USE_LOCAL_API:
        builder = builder.base_url(LOCAL_API_URL)
        builder = builder.base_file_url(LOCAL_API_FILE_URL)
        builder = builder.local_mode(True)
        print(f"🖥️ Local | {human_size(MAX_FILE_SIZE)}")
    else:
        print(f"☁️ Official | {human_size(MAX_FILE_SIZE)}")

    app = builder.post_init(post_init).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("fetch100", fetch100_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CallbackQueryHandler(callback_handler))

    msg_filter = ((filters.TEXT | filters.FORWARDED)
                  & ~filters.COMMAND)
    app.add_handler(MessageHandler(msg_filter, handle_message))
    app.add_error_handler(error_handler)

    logger.info("🤖 Bot starting...")
    print("✅ البوت يعمل!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
