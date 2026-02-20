import asyncio
import logging
import os
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message, BotCommand
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.chat_action import ChatActionSender
from dotenv import load_dotenv

# Add src to python path to import tbank_converter
sys.path.append(str(Path(__file__).parent.parent))

from tbank_converter.pipeline import convert

# Load environment variables
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USERS = [int(uid.strip()) for uid in os.getenv("ALLOWED_USERS", "").split(",") if uid.strip()]

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Temp directory for files
TEMP_DIR = Path(__file__).parent / "temp"
TEMP_DIR.mkdir(exist_ok=True)

class ConversionStates(StatesGroup):
    waiting_for_config = State()

def get_configs_keyboard():
    configs_dir = Path(__file__).parent.parent / "configs"
    buttons = []
    for cfg in configs_dir.glob("*.yaml"):
        icon = "👤"
        if cfg.stem.lower() == "default":
            icon = "⚙️"
        elif "sofya" in cfg.stem.lower():
            icon = "👩"
        elif "valery" in cfg.stem.lower():
            icon = "👨"
        
        buttons.append([InlineKeyboardButton(text=f"{icon} {cfg.stem}", callback_data=f"cfg:{cfg.name}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    logger.info(f"User {message.from_user.full_name} (ID: {message.from_user.id}) sent /start")
    if ALLOWED_USERS and message.from_user.id not in ALLOWED_USERS:
        await message.answer(
            f"❌ <b>Доступ ограничен</b>\n\nВаш ID: <code>{message.from_user.id}</code>\n"
            f"Передайте этот ID администратору для добавления в список разрешенных.",
            parse_mode="HTML"
        )
        return
    
    welcome_text = (
        "👋 <b>Привет! Я бот-конвертер FinancialBot</b>\n\n"
        "Я помогу превратить выписку из Т-Банка в удобный XLSX-файл для Google Таблиц.\n\n"
        "📥 <b>Просто пришлите CSV-файл к сообщению</b>, и мы начнем!"
    )
    await message.answer(welcome_text, parse_mode="HTML")

@dp.message(F.document)
async def handle_document(message: Message, state: FSMContext):
    if ALLOWED_USERS and message.from_user.id not in ALLOWED_USERS:
        return

    if not message.document.file_name.lower().endswith(".csv"):
        await message.answer("⚠️ <b>Пожалуйста, пришлите файл в формате CSV</b>", parse_mode="HTML")
        return

    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        
        local_input_path = TEMP_DIR / f"{message.from_user.id}_{message.document.file_name}"
        await bot.download_file(file_path, local_input_path)
        
        await state.update_data(input_path=str(local_input_path))
        
        await message.answer(
            "📋 <b>Файл получен!</b>\nВыберите конфигурацию настроек:",
            reply_markup=get_configs_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(ConversionStates.waiting_for_config)

@dp.callback_query(F.data.startswith("cfg:"))
async def process_config_selection(callback: types.CallbackQuery, state: FSMContext):
    config_name = callback.data.split(":")[1]
    user_data = await state.get_data()
    input_path_str = user_data.get("input_path")
    
    if not input_path_str:
        await callback.message.answer("❌ Ошибка: данные файла не найдены.")
        await state.clear()
        return
        
    input_path = Path(input_path_str)
    
    if not input_path.exists():
        await callback.message.answer("❌ Ошибка: файл не найден на сервере.")
        await state.clear()
        return

    config_path = Path(__file__).parent.parent / "configs" / config_name
    output_path = input_path.with_suffix(".xlsx")

    await callback.message.edit_text(
        f"⏳ <b>Обработка...</b>\nКонфигурация: <code>{config_name}</code>",
        parse_mode="HTML"
    )

    try:
        async with ChatActionSender.upload_document(bot=bot, chat_id=callback.message.chat.id):
            # Run conversion (blocking call, but for small files it's fine)
            # In production with large files, use run_in_executor
            convert(input_path, output_path, config_path)
            
            # Send result
            await callback.message.answer_document(
                FSInputFile(output_path, filename=output_path.name),
                caption=(
                    f"✅ <b>Готово!</b>\n\n"
                    f"📄 Файл: <code>{output_path.name}</code>\n"
                    f"⚙️ Конфиг: <code>{config_name}</code>"
                ),
                parse_mode="HTML"
            )
            await callback.message.delete()
    except Exception as e:
        logger.exception("Conversion failed")
        await callback.message.answer(f"❌ <b>Ошибка при конвертации:</b>\n<code>{e}</code>", parse_mode="HTML")
    finally:
        # Cleanup
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()
        await state.clear()
        await callback.answer()

async def main():
    if not TOKEN:
        print("Error: BOT_TOKEN is not set in .env file")
        return
        
    # Set bot commands
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота"),
    ])
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
