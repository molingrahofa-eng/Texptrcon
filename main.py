#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت نسخ حزم الملصقات - تحويل من PHP إلى Python
"""

import json
import os
import re
import logging
from typing import Optional

import requests
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InputFile, InputSticker, Sticker,
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters,
)
from telegram.error import TelegramError

# ==================== CONFIG ====================
API_KEY = "6198804155:AAF5Zj-co6guQ6s2bW5hMTvFga8CFRi0WqA"   # ← ضع التوكن هنا
ADMIN_CHAT_ID = 5952132218              # ← (اختياري) معرف الأدمن
DB_FILE = "bot_settings.json"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

EMOJI_RE = re.compile(
    r'[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|'
    r'[\U0001F680-\U0001F6FF]|[\U00002600-\U000026FF]|'
    r'[\U00002700-\U000027BF]'
)


# ==================== 🧩 دالة ربط البوت ====================
def connect_bot(token: str, admin_chat_id: Optional[int] = None) -> Optional[dict]:
    """
    🔌 دالة ربط البوت بالتوكن وايدي الأدمن

    - token: توكن البوت من @BotFather
    - admin_chat_id: (اختياري) معرف الأدمن لاستقبال إشعارات التشغيل

    Returns:
        dict يحتوي على token, bot_id, username, first_name
        أو None في حال فشل الاتصال
    """
    if not token or ":" not in token:
        logger.error("❌ التوكن فارغ أو غير صالح")
        return None

    try:
        # التحقق من صحة التوكن
        r = requests.get(
            f"https://api.telegram.org/bot{token}/getMe",
            timeout=10,
        )
        data = r.json()
        if not data.get("ok"):
            logger.error(f"❌ التوكن غير صالح: {data}")
            return None

        info = {
            "token": token,
            "bot_id": data["result"]["id"],
            "username": data["result"]["username"],
            "first_name": data["result"]["first_name"],
            "admin_chat_id": admin_chat_id,
        }
        logger.info(f"✅ تم الاتصال بالبوت: @{info['username']} (ID: {info['bot_id']})")

        # إشعار الأدمن عند التشغيل (اختياري)
        if admin_chat_id:
            try:
                requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={
                        "chat_id": admin_chat_id,
                        "text": (
                            f"✅ *تم تشغيل البوت بنجاح*\n\n"
                            f"🤖 البوت: @{info['username']}\n"
                            f"🆔 ID: `{info['bot_id']}`"
                        ),
                        "parse_mode": "Markdown",
                    },
                    timeout=10,
                )
            except Exception as e:
                logger.warning(f"تعذّر إرسال إشعار للأدمن: {e}")

        return info

    except requests.exceptions.Timeout:
        logger.error("❌ انتهت مهلة الاتصال بالـ Telegram API")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ خطأ في الاتصال: {e}")
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع: {e}")
    return None


# ==================== 🗄️ التخزين (بديل mys() في PHP) ====================
def load_all() -> dict:
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Load error: {e}")
    return {"default": {}}


def save_all(data: dict) -> None:
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Save error: {e}")


def get_settings() -> dict:
    return load_all().setdefault("default", {})


def save_settings(s: dict) -> None:
    data = load_all()
    data["default"] = s
    save_all(data)


def get_user(chat_id) -> dict:
    return get_settings().get(str(chat_id), {})


def set_user_state(chat_id, **kwargs) -> None:
    s = get_settings()
    cid = str(chat_id)
    s.setdefault(cid, {}).update(kwargs)
    save_settings(s)


def clear_user(chat_id) -> None:
    s = get_settings()
    s.pop(str(chat_id), None)
    save_settings(s)


# ==================== 🛠️ أدوات مساعدة ====================
def is_emoji(text: str) -> bool:
    return bool(text and EMOJI_RE.search(text))


def btn(text: str, cb: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text, callback_data=cb)


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[btn("• رجوع '🔙،", "backstiker")]])


async def safe_edit(query, text: str, kb=None) -> None:
    try:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)
    except TelegramError as e:
        logger.error(f"edit error: {e}")


async def download_file(context, file_id: str, path: str) -> bool:
    try:
        tg_file = await context.bot.get_file(file_id)
        await tg_file.download_to_drive(path)
        return True
    except Exception as e:
        logger.error(f"download error: {e}")
        return False


async def sticker_set_exists(context, name: str) -> bool:
    try:
        await context.bot.get_sticker_set(name=name)
        return True
    except TelegramError:
        return False


# ==================== /start ====================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    name = user.first_name or "صديقي"
    usem = f"@{user.username}" if user.username else "بدون"

    settings = get_settings()
    welcome = settings.get("wellcom")

    if not welcome:
        start_text = (
            f"*اهلا بك* {name}\n\n"
            "*في بوت نسخ حزم ملصقات واضافه الملصقات عليها\n"
            "اضغط نسخ حزمه الان للحصول على حزمه ✅..*\n—————"
        )
    else:
        start_text = (
            welcome
            .replace("#name", name)
            .replace("#username", usem)
            .replace("#id", str(user.id))
        )

    keyboard = [
        [btn(" نسخ حزمه 📊", "AddS"), btn("حزماتي 📮", "ETAdd")],
        [btn("الحصول على صور الحزمه 🧸", "boto")],
        [btn("الحصول على ملفات الحزمه 🖤", "file")],
    ]

    await update.message.reply_text(
        start_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True,
    )
    set_user_state(chat_id, set="weelldone")


# ==================== 📩 Callback Handler ====================
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    chat_id = q.from_user.id
    data = q.data or ""

    # ---- الرجوع للقائمة ----
    if data == "backstiker":
        user = q.from_user
        name = user.first_name or "صديقي"
        text = (
            f"*اهلا بك* {name}\n\n"
            "*في بوت نسخ حزم ملصقات واضافه الملصقات عليها\n"
            "اضغط نسخ حزمه الان للحصول على حزمه ✅..*"
        )
        kb = InlineKeyboardMarkup([
            [btn(" نسخ حزمه 📊", "AddS"), btn("حزماتي 📮", "ETAdd")],
            [btn("الحصول على صور الحزمه 🖤", "boto")],
            [btn("الحصول على ملفات الحزمه 🧸", "file")],
        ])
        await safe_edit(q, text, kb)
        set_user_state(chat_id, set="weelldone")
        return

    # ---- لوحة الأدمن ----
    if data == "toch":
        kb = InlineKeyboardMarkup([
            [btn("جلب نسخه 🗳", "geet")],
            [btn("رجوع", "backstiker")],
        ])
        await safe_edit(
            q,
            "*⚙: اهلا بك عزيزي\n\nفي لوحه الاوامر ألخاصة لبوت الملصقات*",
            kb,
        )
        return

    # ---- إعدادات الترحيب ----
    if data == "what":
        settings = get_settings()
        start_msg = settings.get("wellcom", "غير معيّنة")
        kb = InlineKeyboardMarkup([
            [btn("تعين الرساله", "pthi"), btn("مسح الرساله", "delhi")],
            [btn("رجوع", "backstiker")],
        ])
        await safe_edit(
            q,
            f"• *مرحبا بك في قسم رساله الترحيب* (/start) 🌾\n"
            f"- ستظهر هذه الرساله عند ارسال (/start)\n\n"
            f"• رسالة الترحيب :\n\n`{start_msg}`",
            kb,
        )
        return

    if data == "pthi":
        await safe_edit(q, "*ارسل رسالة الترحيب الجديدة الآن ✅*", back_kb())
        set_user_state(chat_id, set="set_welcome")
        return

    if data == "delhi":
        settings = get_settings()
        settings.pop("wellcom", None)
        save_settings(settings)
        await safe_edit(q, "*تم مسح رسالة الترحيب ✅*", back_kb())
        return

    # ---- ملفات الحزمة ----
    if data == "file":
        await safe_edit(q, "*📨 ارسل الملصق لاقوم بارسال الملفات لك *", back_kb())
        set_user_state(chat_id, set="file")
        return

    # ---- صور الحزمة ----
    if data == "boto":
        await safe_edit(q, "*📨 ارسل الملصق لاقوم بارسال الصور لك *", back_kb())
        set_user_state(chat_id, set="getphoto")
        return

    # ---- بدء نسخ حزمة ----
    if data == "AddS":
        await safe_edit(q, "*ارسل اسم الحزمه الان ✅*", back_kb())
        set_user_state(chat_id, set="AddS_1")
        return

    # ---- حزماتي ----
    if data == "ETAdd":
        settings = get_settings()
        user_sets = settings.get(f"S{chat_id}", [])
        if not user_sets:
            await q.answer("لا تملك حزم ملصقات داخل البوت ⚠️", show_alert=True)
            return
        rows = [[btn(s, f"dll#{s}"), btn("تعديل", f"dll#{s}")] for s in user_sets]
        rows.append([btn("• رجوع '🔙،", "backstiker")])
        await safe_edit(
            q,
            "🧸 ⌯ *اهلا بك في قائمه حزماتك*\n💕 ⌯ *اختر اسم الحزمه التي تريد التعديل عليها*",
            InlineKeyboardMarkup(rows),
        )
        return

    # ---- إدارة حزمة ----
    if data.startswith("dll#"):
        set_name = data.split("#", 1)[1]
        username = context.bot_data["bot_info"]["username"]
        link = f"http://t.me/addstickers/{set_name}_by_{username}"
        kb = InlineKeyboardMarkup([
            [btn("حذف ملصق", f"delSte#{set_name}"), btn("اضافه ملصق", f"adSte#{set_name}")],
            [btn("تغيير صوره الحزمه", f"ETS#{set_name}"), btn("حذف الحزمه", f"ddlp#{set_name}")],
            [btn("• رجوع '🔙،", "backstiker")],
        ])
        await safe_edit(q, f"🖤 ⌯ سيتم الان تعديل على الحزمه التاليه :\n*{link}*", kb)
        return

    # ---- حذف الحزمة ----
    if data.startswith("ddlp#"):
        set_name = data.split("#", 1)[1]
        settings = get_settings()
        key = f"S{chat_id}"
        sets = settings.get(key, [])
        if set_name in sets:
            sets.remove(set_name)
            settings[key] = sets
            save_settings(settings)
        await safe_edit(
            q,
            "تم حذف الحزمة من البوت ✅\n"
            "يمكنك حذف الحزمة نهائيا من خلال الذهاب الى البوت الرسمي\n"
            "*@Stickers* وارسال `/delpack` واتبع التعليمات 🧸.",
            back_kb(),
        )
        return

    # ---- تغيير الصورة ----
    if data.startswith("ETS#"):
        set_name = data.split("#", 1)[1]
        await safe_edit(q, "*ارسل الان الصوره الجديده للحزمه ✅*", back_kb())
        set_user_state(chat_id, set="ETS_1", name=set_name)
        return

    # ---- حذف ملصق ----
    if data.startswith("delSte#"):
        set_name = data.split("#", 1)[1]
        username = context.bot_data["bot_info"]["username"]
        link = f"http://t.me/addstickers/{set_name}_by_{username}"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("اختر ملصق", url=link)],
            [btn("• رجوع '🔙،", "backstiker")],
        ])
        await safe_edit(q, "*ارسل الملصق الان ✅*", kb)
        set_user_state(chat_id, set="delSte_1", name=set_name)
        return

    # ---- إضافة ملصق ----
    if data.startswith("adSte#"):
        set_name = data.split("#", 1)[1]
        await safe_edit(q, "*ارسل الاموجي 🧸💕*", back_kb())
        set_user_state(chat_id, set="adSte_1", name=set_name)
        return


# ==================== ✉️ Message Handler ====================
async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    chat_id = msg.chat_id
    text = msg.text or ""
    user_data = get_user(chat_id)
    state = user_data.get("set", "")
    set_name = user_data.get("name", "")
    bot_username = context.bot_data["bot_info"]["username"]

    # ===== ملصقات =====
    if msg.sticker:
        if state == "file":
            await send_set_files(update, context, msg.sticker.set_name); return
        if state == "getphoto":
            await send_set_photos(update, context, msg.sticker.set_name); return
        if state == "delSte_1":
            await delete_sticker(update, context, msg.sticker, set_name, bot_username); return
        if state == "adSte_2":
            await add_sticker_from_sticker(update, context, msg.sticker, user_data, bot_username); return
        if state == "AddS_3":
            await copy_sticker_set(update, context, msg.sticker.set_name, user_data, bot_username); return

    # ===== صور =====
    if msg.photo:
        if state == "ETS_1":
            await change_thumbnail(update, context, msg.photo[-1].file_id, set_name, bot_username); return
        if state == "adSte_2":
            await add_sticker_from_photo(update, context, msg.photo[-1].file_id, user_data, bot_username); return

    # ===== نصوص =====
    if not text:
        return

    if state == "set_welcome":
        settings = get_settings()
        settings["wellcom"] = text
        save_settings(settings)
        await msg.reply_text("*تم حفظ رسالة الترحيب ✅*", parse_mode="Markdown", reply_markup=back_kb())
        clear_user(chat_id)
        return

    if state == "adSte_1":
        if is_emoji(text):
            set_user_state(chat_id, emojis=text, set="adSte_2")
            await msg.reply_text(
                "*\nالان قم بارسل صوره\nاو قم بأرسال ملصق من ملصقاتك*",
                parse_mode="Markdown",
                reply_markup=back_kb(),
            )
        else:
            await msg.reply_text("*ارسل اسمايل فقط ✅*", parse_mode="Markdown", reply_markup=back_kb())
        return

    if state == "AddS_1":
        set_user_state(chat_id, title=text, set="AddS_2")
        await msg.reply_text("*ارسل رابط الحزمه أو اسمها المختصر ✅*", parse_mode="Markdown", reply_markup=back_kb())
        return

    if state == "AddS_2":
        slug = text.strip()
        if "/addstickers/" in slug:
            slug = slug.split("/addstickers/")[-1]
        slug = slug.split("_by_")[0].split("?")[0].strip()
        if not re.match(r'^[a-zA-Z0-9_]+$', slug):
            await msg.reply_text(
                "*اسم غير صالح. استخدم حروف إنجليزية وأرقام فقط* ⚠️",
                parse_mode="Markdown",
                reply_markup=back_kb(),
            )
            return
        settings = get_settings()
        settings.setdefault(f"S{chat_id}", []).append(slug)
        save_settings(settings)
        set_user_state(chat_id, name=slug, set="AddS_3")
        await msg.reply_text(
            "*ارسل ملصق من الحزمة المراد نسخها ✅*",
            parse_mode="Markdown",
            reply_markup=back_kb(),
        )
        return


# ==================== ⚙️ تنفيذ الأوامر ====================

async def send_set_files(update, context, set_name: str):
    chat_id = update.effective_chat.id
    try:
        sticker_set = await context.bot.get_sticker_set(name=set_name)
    except TelegramError as e:
        await update.message.reply_text(f"⚠️ خطأ: {e}"); return

    for i, st in enumerate(sticker_set.stickers):
        path = f"{chat_id}_{i}.png"
        if await download_file(context, st.file_id, path):
            try:
                with open(path, "rb") as f:
                    await context.bot.send_document(
                        chat_id=chat_id,
                        document=InputFile(f, filename=f"sticker_{i}.png"),
                    )
            finally:
                os.path.exists(path) and os.remove(path)

    set_user_state(chat_id, set="done")
    await update.message.reply_text(
        "*تم الانتهاء من ارسال الملفات ✅*",
        parse_mode="Markdown", reply_markup=back_kb(),
    )


async def send_set_photos(update, context, set_name: str):
    chat_id = update.effective_chat.id
    try:
        sticker_set = await context.bot.get_sticker_set(name=set_name)
    except TelegramError as e:
        await update.message.reply_text(f"⚠️ خطأ: {e}"); return

    for i, st in enumerate(sticker_set.stickers):
        path = f"{chat_id}_{i}.png"
        if await download_file(context, st.file_id, path):
            try:
                with open(path, "rb") as f:
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=InputFile(f, filename=f"sticker_{i}.png"),
                    )
            finally:
                os.path.exists(path) and os.remove(path)

    set_user_state(chat_id, set="done")
    await update.message.reply_text(
        "*تم الانتهاء من ارسال الصور ✅*",
        parse_mode="Markdown", reply_markup=back_kb(),
    )


async def delete_sticker(update, context, sticker: Sticker, set_name: str, bot_username: str):
    chat_id = update.effective_chat.id
    try:
        await context.bot.delete_sticker_from_set(sticker=sticker.file_id)
        link = f"http://t.me/addstickers/{set_name}_by_{bot_username}"
        await update.message.reply_text(f"تم حذف الملصق من:\n{link}", reply_markup=back_kb())
        clear_user(chat_id)
    except TelegramError as e:
        await update.message.reply_text(f"⚠️ خطأ: {e}")


async def add_sticker_from_sticker(update, context, sticker: Sticker, user_data, bot_username):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    set_name = user_data.get("name", "")
    emoji = user_data.get("emojis", "😀")
    path = f"{chat_id}_ad.png"
    try:
        if not await download_file(context, sticker.file_id, path):
            raise Exception("فشل تنزيل الملصق")
        with open(path, "rb") as f:
            uploaded = await context.bot.upload_sticker_file(
                user_id=user_id,
                sticker=InputFile(f, filename="sticker.png"),
                sticker_format="static",
            )
        await context.bot.add_sticker_to_set(
            user_id=user_id,
            name=f"{set_name}_by_{bot_username}",
            sticker=InputSticker(sticker=uploaded.file_id, emoji_list=[emoji]),
        )
        os.remove(path)
        link = f"http://t.me/addstickers/{set_name}_by_{bot_username}"
        kb = InlineKeyboardMarkup([
            [btn("اضافه ملصق جديد", f"adSte#{set_name}")],
            [btn("• رجوع '🔙،", "backstiker")],
        ])
        await update.message.reply_text(f"تم اضافه الملصق الى:\n{link}", reply_markup=kb)
        clear_user(chat_id)
    except Exception as e:
        logger.error(f"add sticker error: {e}")
        await update.message.reply_text(f"⚠️ فشل: {e}")
        os.path.exists(path) and os.remove(path)


async def add_sticker_from_photo(update, context, file_id: str, user_data, bot_username):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    set_name = user_data.get("name", "")
    emoji = user_data.get("emojis", "😀")
    path = f"{chat_id}_ad.png"
    try:
        if not await download_file(context, file_id, path):
            raise Exception("فشل تنزيل الصورة")
        with open(path, "rb") as f:
            uploaded = await context.bot.upload_sticker_file(
                user_id=user_id,
                sticker=InputFile(f, filename="sticker.png"),
                sticker_format="static",
            )
        await context.bot.add_sticker_to_set(
            user_id=user_id,
            name=f"{set_name}_by_{bot_username}",
            sticker=InputSticker(sticker=uploaded.file_id, emoji_list=[emoji]),
        )
        os.remove(path)
        link = f"http://t.me/addstickers/{set_name}_by_{bot_username}"
        kb = InlineKeyboardMarkup([
            [btn("اضافه ملصق جديد", f"adSte#{set_name}")],
            [btn("• رجوع '🔙،", "backstiker")],
        ])
        await update.message.reply_text(f"تم اضافه الملصق الى:\n{link}", reply_markup=kb)
        clear_user(chat_id)
    except Exception as e:
        logger.error(f"add photo error: {e}")
        await update.message.reply_text(f"⚠️ فشل: {e}")
        os.path.exists(path) and os.remove(path)


async def change_thumbnail(update, context, file_id: str, set_name: str, bot_username: str):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    path = f"{chat_id}_thumb.png"
    try:
        if not await download_file(context, file_id, path):
            raise Exception("فشل تنزيل الصورة")
        with open(path, "rb") as f:
            await context.bot.set_sticker_set_thumb(
                name=f"{set_name}_by_{bot_username}",
                user_id=user_id,
                thumbnail=InputFile(f, filename="thumb.png"),
            )
        os.remove(path)
        link = f"http://t.me/addstickers/{set_name}_by_{bot_username}"
        await update.message.reply_text(f"تم تغيير صوره الحزمه بنجاح:\n{link}", reply_markup=back_kb())
        clear_user(chat_id)
    except Exception as e:
        logger.error(f"thumbnail error: {e}")
        await update.message.reply_text(f"⚠️ فشل: {e}")
        os.path.exists(path) and os.remove(path)


async def copy_sticker_set(update, context, source_name: str, user_data, bot_username):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    slug = user_data.get("name", "")
    title = user_data.get("title", "Copied Pack")
    full_new_name = f"{slug}_by_{bot_username}"

    await update.message.reply_text(
        "*جاري نسخ الحزمه :\nلطفا يرجى الانتظار لحين اكتمال النسخ\nلا تقم بارسال شيء حتى يتم الانتهاء لطفا 💕*",
        parse_mode="Markdown",
    )

    try:
        original = await context.bot.get_sticker_set(name=source_name)
    except TelegramError as e:
        await update.message.reply_text(f"⚠️ فشل جلب الحزمة: {e}")
        return

    created = False
    count = 0

    for i, st in enumerate(original.stickers):
        path = f"{chat_id}_copy_{i}.png"
        try:
            if not await download_file(context, st.file_id, path):
                continue
            with open(path, "rb") as f:
                uploaded = await context.bot.upload_sticker_file(
                    user_id=user_id,
                    sticker=InputFile(f, filename="sticker.png"),
                    sticker_format="static",
                )
            item = InputSticker(sticker=uploaded.file_id, emoji_list=[st.emoji or "😀"])
            if not created:
                try:
                    await context.bot.create_new_sticker_set(
                        user_id=user_id,
                        name=full_new_name,
                        title=title,
                        stickers=[item],
                        sticker_format="static",
                    )
                    created = True
                except TelegramError:
                    try:
                        await context.bot.add_sticker_to_set(user_id, full_new_name, item)
                        created = True
                    except Exception as e2:
                        logger.error(f"add fallback error: {e2}")
            else:
                try:
                    await context.bot.add_sticker_to_set(user_id, full_new_name, item)
                except TelegramError as e:
                    logger.error(f"add error at {i}: {e}")
            count += 1
        except Exception as e:
            logger.error(f"copy error at {i}: {e}")
        finally:
            os.path.exists(path) and os.remove(path)

    link = f"http://t.me/addstickers/{full_new_name}"
    kb = InlineKeyboardMarkup([
        [btn("اعدادات الحزم", "ETAdd")],
        [btn("• رجوع '🔙،", "backstiker")],
    ])
    await update.message.reply_text(
        f"تم انشاء الحزمه\n---\n"
        f"اسم الحزمه : {title}\n"
        f"رابط الحزمه :\n{link}\n\n"
        f"عدد الملصقات المنسوخة: {count}",
        reply_markup=kb,
    )
    set_user_state(chat_id, set="done")


# ==================== 🚀 MAIN ====================
def main():
    # 🔌 1) ربط البوت
    bot_info = connect_bot(API_KEY, admin_chat_id=ADMIN_CHAT_ID)
    if not bot_info:
        logger.error("❌ توقف: فشل الاتصال بالبوت. تحقق من التوكن.")
        return

    # 🏗️ 2) بناء التطبيق
    app = Application.builder().token(API_KEY).build()
    app.bot_data["bot_info"] = bot_info

    # 📌 3) تسجيل المعالجات
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, on_message))

    # ▶️ 4) التشغيل
    logger.info("🚀 البوت يعمل الآن...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
