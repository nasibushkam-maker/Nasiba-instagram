import asyncio
import logging
import os
import re
import time
import uuid
from pathlib import Path
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ChatAction
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import yt_dlp
import converter

# Логларни созлаш
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# .env файлидан созламаларни юклаш
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.critical("=" * 60)
    logger.critical("ХАТОЛИК: BOT_TOKEN топилмади!")
    logger.critical("Render бошқарув панелида Environment бўлимига ўтинг ва BOT_TOKEN калитини қўшинг!")
    logger.critical("=" * 60)
    raise ValueError("BOT_TOKEN топилмади! Render'да Environment Variables'га BOT_TOKEN ни киритинг.")

# Папкалар
DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Instagram ҳаволалари учун мунтазам ифода (Regex)
INSTAGRAM_REGEX = re.compile(
    r"https?:\/\/(?:www\.)?instagram\.com\/(?:p|reel|reels|tv|share\/reel|share\/p)\/[A-Za-z0-9_\-]+[^\s]*",
    re.IGNORECASE,
)

# Вақтинчалик файлларни хотирада сақлаш (token -> {path, name, created_at})
PENDING_FILES = {}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ==========================================
# 1. INSTAGRAM ЮКЛАШ ФУНКЦИЯСИ
# ==========================================
def download_instagram_video(url: str) -> str:
    file_prefix = f"ig_{uuid.uuid4().hex[:10]}"
    output_template = str(DOWNLOADS_DIR / f"{file_prefix}.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "merge_output_format": "mp4",
        "socket_timeout": 30,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            raise ValueError("Видео маълумотларини олиб бўлмади.")

        filename = ydl.prepare_filename(info)
        base_path, _ = os.path.splitext(filename)
        mp4_path = f"{base_path}.mp4"
        if os.path.exists(mp4_path):
            return mp4_path
        if os.path.exists(filename):
            return filename

        matching = list(DOWNLOADS_DIR.glob(f"{file_prefix}.*"))
        if matching:
            return str(matching[0])

        raise FileNotFoundError("Юкланган видео файли топилмади.")


# ==========================================
# 2. АСОСИЙ БУЙРУҚЛАР (/start, /help)
# ==========================================
@dp.message(CommandStart())
async def handle_start(message: types.Message):
    greeting = (
        f"Ассалому алайкум, <b>{message.from_user.full_name}</b>!\n\n"
        "🤖 <b>Ушбу бот 2 та асосий функцияга эга:</b>\n\n"
        "1️⃣ <b>Instagram видео юклаш:</b>\n"
        "   Instagram'дан исталган Reels, Post ёки IGTV ҳаволасини юборинг.\n\n"
        "2️⃣ <b>Ҳар қандай файл форматини ўзгартириш (Конвертер):</b>\n"
        "   Ботга исталган файлни юборинг (Расм, Аудио, Видео ёки Ҳужжат) ва "
        "керакли формат тугмасини танланг!\n\n"
        "Қўллаб-қувватланадиган форматлар:\n"
        "• Excel ва жадваллар: XLSX, XLS, CSV\n"
        "• Ҳужжатлар: PDF, DOCX, TXT\n"
        "• Расмлар: PNG, JPG, WEBP, BMP, ICO\n"
        "• Аудио ва Видео: MP3, WAV, GIF, MP4 ва бошқалар."
    )
    await message.answer(greeting, parse_mode="HTML")


@dp.message(Command("help"))
async def handle_help(message: types.Message):
    help_text = (
        "ℹ️ <b>Қўлланма:</b>\n\n"
        "🔹 <b>Видео юклаш учун:</b>\n"
        "Instagram'дан видео ҳаволасидан нусха олиб ботга ташланг.\n\n"
        "🔹 <b>Файл форматини ўзгартириш учун:</b>\n"
        "Ботга расм, ҳужжат, аудио ёки видео файлини юборинг. Бот сизга мос форматлар "
        "рўйхатини тугмалар шаклида тақдим этади. Керакли тугмани босишингиз билан "
        "тайёр файл сизга қайтарилади."
    )
    await message.answer(help_text, parse_mode="HTML")


# ==========================================
# 3. INSTAGRAM ҲАВОЛАЛАРИНИ ҚАБУЛ ҚИЛИШ
# ==========================================
@dp.message(F.text.regexp(INSTAGRAM_REGEX))
async def handle_instagram_link(message: types.Message):
    url_match = INSTAGRAM_REGEX.search(message.text)
    if not url_match:
        await message.reply("Илтимос, ҳақиқий Instagram ҳаволасини юборинг.")
        return

    url = url_match.group(0)
    status_msg = await message.reply("⏳ Видео юклаб олинмоқда, илтимос кутинг...")

    downloaded_file = None
    try:
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_VIDEO)
        downloaded_file = await asyncio.to_thread(download_instagram_video, url)

        file_size_mb = os.path.getsize(downloaded_file) / (1024 * 1024)
        if file_size_mb > 50:
            await status_msg.edit_text(
                f"❌ Видео ҳажми ({file_size_mb:.1f} MB) жуда катта.\n"
                "Телеграм Бот API 50 MB гача бўлган файлларни қўллаб-қувватлайди."
            )
            return

        await status_msg.edit_text("📤 Видео Телеграмга юборилмоқда...")
        video_input = FSInputFile(downloaded_file)

        await message.reply_video(
            video=video_input,
            caption="🎬 @Instagram орқали юкланди",
            supports_streaming=True,
        )
        await status_msg.delete()

    except Exception as e:
        logger.error(f"Instagram юклашда хатолик: {e}", exc_info=True)
        await status_msg.edit_text(
            "❌ Видеони юклаб олишда хатолик юз берди.\n\n"
            "Эҳтимолий сабаблар:\n"
            "• Аккаунт ёпиқ (Private) бўлиши мумкин\n"
            "• Ҳавола нотўғри ёки ўчириб ташланган"
        )
    finally:
        if downloaded_file and os.path.exists(downloaded_file):
            try:
                os.remove(downloaded_file)
            except OSError:
                pass


# ==========================================
# 4. ФАЙЛ ҚАБУЛ ҚИЛИШ ВА КОНВЕРТАЦИЯГА ТАЙЁРЛАШ
# ==========================================
async def process_incoming_file(message: types.Message, file_id: str, original_name: str, file_size: int):
    # Telegram Bot API лимити: 20MB (Бот орқали файлни юклаб олиш чеклови)
    if file_size > 20 * 1024 * 1024:
        await message.reply(
            "❌ Кечирасиз, файл ҳажми 20 MB дан ошмаслиги керак (Telegram Bot API чеклови)."
        )
        return

    _, ext = os.path.splitext(original_name)
    if not ext:
        ext = ".jpg"  # Стандарт расмлар учун

    formats = converter.get_available_target_formats(ext)
    if not formats:
        await message.reply(
            f"ℹ️ <code>{ext}</code> формати учун мос конвертация топилмади.\n"
            "Бот қуйидагиларни қўллайди: PNG, JPG, WEBP, PDF, DOCX, TXT, MP3, WAV, GIF ва бошқалар.",
            parse_mode="HTML"
        )
        return

    status_msg = await message.reply("⏳ Файл қабул қилинмоқда...")

    token = uuid.uuid4().hex[:8]
    local_filename = f"{token}_{original_name}"
    local_path = str(UPLOADS_DIR / local_filename)

    # Телеграм серверларидан файлни юклаб олиш
    file_info = await bot.get_file(file_id)
    await bot.download_file(file_info.file_path, destination=local_path)

    # Хотирада вақтинча сақлаш
    PENDING_FILES[token] = {
        "path": local_path,
        "name": original_name,
        "ext": ext,
        "created_at": time.time(),
    }

    # Клавиатура тузиш
    builder = InlineKeyboardBuilder()
    for label, target_fmt in formats:
        builder.button(text=label, callback_data=f"cv:{token}:{target_fmt}")
    builder.adjust(2)
    # Бекор қилиш тугмаси
    builder.row(types.InlineKeyboardButton(text="❌ Бекор қилиш", callback_data=f"cv_cancel:{token}"))

    size_mb = file_size / (1024 * 1024)
    size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{file_size / 1024:.1f} KB"

    caption_text = (
        f"📂 <b>Файл қабул қилинди:</b> <code>{original_name}</code> ({size_str})\n\n"
        f"💡 Ушбу файлни қайси форматга ўзгартирмоқчисиз?\n"
        f"Керакли форматни танланг:"
    )

    await status_msg.edit_text(caption_text, reply_markup=builder.as_markup(), parse_mode="HTML")


@dp.message(F.photo)
async def handle_photo(message: types.Message):
    """Фойдаланувчи расм юборганда"""
    photo = message.photo[-1]  # Энг сифатли ўлчам
    original_name = f"photo_{photo.file_unique_id}.jpg"
    await process_incoming_file(message, photo.file_id, original_name, photo.file_size or 0)


@dp.message(F.document)
async def handle_document(message: types.Message):
    """Фойдаланувчи ҳужжат/файл юборганда"""
    doc = message.document
    original_name = doc.file_name or f"document_{doc.file_unique_id}"
    await process_incoming_file(message, doc.file_id, original_name, doc.file_size or 0)


@dp.message(F.audio)
async def handle_audio(message: types.Message):
    """Фойдаланувчи аудио файл юборганда"""
    audio = message.audio
    original_name = audio.file_name or f"audio_{audio.file_unique_id}.mp3"
    await process_incoming_file(message, audio.file_id, original_name, audio.file_size or 0)


@dp.message(F.voice)
async def handle_voice(message: types.Message):
    """Фойдаланувчи овозли хабар юборганда"""
    voice = message.voice
    original_name = f"voice_{voice.file_unique_id}.ogg"
    await process_incoming_file(message, voice.file_id, original_name, voice.file_size or 0)


@dp.message(F.video)
async def handle_video(message: types.Message):
    """Фойдаланувчи видео юборганда"""
    video = message.video
    original_name = video.file_name or f"video_{video.file_unique_id}.mp4"
    await process_incoming_file(message, video.file_id, original_name, video.file_size or 0)


# ==========================================
# 5. КОНВЕРТАЦИЯ ТУГМАЛАРИНИ ИШЛАШИ (CALLBACK)
# ==========================================
@dp.callback_query(F.data.startswith("cv_cancel:"))
async def handle_conversion_cancel(callback: CallbackQuery):
    token = callback.data.split(":")[1]
    file_data = PENDING_FILES.pop(token, None)
    if file_data and os.path.exists(file_data["path"]):
        try:
            os.remove(file_data["path"])
        except OSError:
            pass

    await callback.message.edit_text("❌ Конвертация бекор қилинди.")
    await callback.answer("Бекор қилинди")


@dp.callback_query(F.data.startswith("cv:"))
async def handle_conversion_action(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Хато сўров.")
        return

    _, token, target_format = parts
    file_data = PENDING_FILES.pop(token, None)

    if not file_data or not os.path.exists(file_data["path"]):
        await callback.message.edit_text("⚠️ Файл муддати тугаган ёки топилмади. Илтимос, қайта юборинг.")
        await callback.answer()
        return

    input_path = file_data["path"]
    orig_name = file_data["name"]

    await callback.message.edit_text(
        f"⏳ <b>{orig_name}</b> файли <b>{target_format.upper()}</b> форматига ўгирилмоқда...\n"
        f"Илтимос, бироз кутинг...",
        parse_mode="HTML"
    )
    await callback.answer("Конвертация бошланди...")

    converted_path = None
    try:
        # Конвертация алоҳида thread'да бажарилади
        converted_path = await asyncio.to_thread(converter.convert_file, input_path, target_format)

        if not os.path.exists(converted_path):
            raise FileNotFoundError("Конвертация қилинган файл яратилмади.")

        base_orig, _ = os.path.splitext(orig_name)
        new_ext = os.path.splitext(converted_path)[1]
        final_filename = f"{base_orig}{new_ext}"

        result_file = FSInputFile(converted_path, filename=final_filename)

        caption = f"✅ <b>{orig_name}</b> муваффақиятли <b>{new_ext.upper()}</b> форматига ўтказилди!"

        # Файл турига мос равишда юбориш
        if new_ext.lower() in (".jpg", ".jpeg", ".png", ".webp"):
            await callback.message.reply_document(document=result_file, caption=caption, parse_mode="HTML")
        elif new_ext.lower() in (".mp3", ".wav", ".m4a", ".aac", ".ogg"):
            await callback.message.reply_audio(audio=result_file, caption=caption, parse_mode="HTML")
        elif new_ext.lower() == ".gif":
            await callback.message.reply_animation(animation=result_file, caption=caption, parse_mode="HTML")
        else:
            await callback.message.reply_document(document=result_file, caption=caption, parse_mode="HTML")

        await callback.message.delete()

    except Exception as e:
        logger.error(f"Конвертация хатоси: {e}", exc_info=True)
        await callback.message.edit_text(
            f"❌ Конвертация қилишда хатолик юз берди: {str(e)[:150]}\n"
            f"Файл бузилган бўлиши ёки ушбу форматга тўлиқ мос келмаслиги мумкин."
        )
    finally:
        # Вақтинчалик файлларни тозалаш
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except OSError:
                pass
        if converted_path and os.path.exists(converted_path):
            try:
                os.remove(converted_path)
            except OSError:
                pass


# ==========================================
# 6. БОШҚА ХАБАРЛАР
# ==========================================
@dp.message()
async def handle_other_messages(message: types.Message):
    await message.reply(
        "👋 Мен сизга қуйидаги икки хизматни таклиф қиламан:\n\n"
        "1️⃣ <b>Instagram видео юклаш:</b> Видео ҳаволасини юборинг (Reels, Post).\n"
        "2️⃣ <b>Файл форматини ўзгартириш:</b> Расм, аудио, видео ёки ҳужжат юборинг.\n\n"
        "Илтимос, ҳавола ёки файл ташланг!",
        parse_mode="HTML"
    )


# ==========================================
# 7. RENDER УЧУН ДАСТУР (HEALTH CHECK HTTP СЕРВЕР)
# ==========================================
async def start_dummy_server(port: int):
    """
    Render'да Web Service бепул тарифида порт скан хатолиги
    (Port scan timeout) бермаслиги учун енгил HTTP сервер.
    """
    from aiohttp import web
    app = web.Application()

    async def handle_ping(request):
        return web.Response(text="Bot is running! 🚀\nTelegram: @nasiba_instagram_bot")

    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Render HTTP сервери {port}-портда муваффақиятли ишга тушди.")


async def main():
    logger.info("Бот кўп функцияли режимда ишга тушмоқда...")
    await bot.delete_webhook(drop_pending_updates=True)

    # Render муҳитида PORT мавжуд бўлса, HTTP серверни ишга тушириш
    port_env = os.getenv("PORT")
    if port_env:
        try:
            port = int(port_env)
            await start_dummy_server(port)
        except Exception as e:
            logger.warning(f"Render HTTP серверини ишга туширишда хатолик: {e}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот тўхтатилди.")

