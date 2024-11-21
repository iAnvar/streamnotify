import os
import asyncio
import logging
from telethon import TelegramClient, events
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
from flask import Flask, request

# Настройки логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID')  # ВАШ ЛИЧНЫЙ CHAT ID

# Список для мониторинга каналов
MONITORED_CHANNELS = []

# Создаем Flask приложение
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает", 200

# Клиент для мониторинга стримов
client = TelegramClient('session', API_ID, API_HASH)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    # Логирование для диагностики
    logger.info(f"Start command received. Chat ID: {chat_id}, Chat Type: {chat_type}")
    
    await update.message.reply_text(f'Привет! Твой Chat ID: {chat_id}, Тип чата: {chat_type}')

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавление канала в список мониторинга"""
    # Проверка прав администратора
    if update.effective_user.id != int(ADMIN_CHAT_ID):
        await update.message.reply_text('У вас нет прав для этой команды.')
        return

    if not context.args:
        await update.message.reply_text('Пожалуйста, укажите username канала')
        return

    channel_username = context.args[0]
    MONITORED_CHANNELS.append(channel_username)
    
    # Логирование для диагностики
    logger.info(f"Канал {channel_username} добавлен в список мониторинга")
    
    await update.message.reply_text(f'Канал {channel_username} добавлен в список мониторинга')

async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список мониторируемых каналов"""
    # Проверка прав администратора
    if update.effective_user.id != int(ADMIN_CHAT_ID):
        await update.message.reply_text('У вас нет прав для этой команды.')
        return

    if not MONITORED_CHANNELS:
        await update.message.reply_text('Список мониторинга пуст.')
    else:
        channels_list = '\n'.join(MONITORED_CHANNELS)
        await update.message.reply_text(f'Мониторируемые каналы:\n{channels_list}')

async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление канала из списка мониторинга"""
    # Проверка прав администратора
    if update.effective_user.id != int(ADMIN_CHAT_ID):
        await update.message.reply_text('У вас нет прав для этой команды.')
        return

    if not context.args:
        await update.message.reply_text('Пожалуйста, укажите username канала')
        return

    channel_username = context.args[0]
    if channel_username in MONITORED_CHANNELS:
        MONITORED_CHANNELS.remove(channel_username)
        await update.message.reply_text(f'Канал {channel_username} удален из списка мониторинга')
    else:
        await update.message.reply_text('Канал не найден в списке мониторинга')

async def monitor_streams(application):
    """Мониторинг стримов в указанных каналах"""
    async with client:
        @client.on(events.NewMessage(chats=MONITORED_CHANNELS))
        async def stream_handler(event):
            # Простая логика определения стрима
            if '#live' in event.message.text:
                try:
                    await application.bot.send_message(
                        chat_id=ADMIN_CHAT_ID, 
                        text=f'Начался стрим в канале {event.chat.username}!'
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки сообщения: {e}")

async def main():
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_channel", add_channel))
    application.add_handler(CommandHandler("remove_channel", remove_channel))
    application.add_handler(CommandHandler("list_channels", list_channels))

    # Запуск бота и клиента
    await application.initialize()
    await application.start()
    
    # Запуск мониторинга стримов
    await monitor_streams(application)
    
    await application.updater.start_polling()

# Обновленный запуск для Render
if __name__ == '__main__':
    import threading

    def run_bot():
        asyncio.run(main())

    def run_flask():
        from waitress import serve
        serve(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

    # Запускаем бота и Flask в разных потоках
    bot_thread = threading.Thread(target=run_bot)
    flask_thread = threading.Thread(target=run_flask)

    bot_thread.start()
    flask_thread.start()

    bot_thread.join()
    flask_thread.join()