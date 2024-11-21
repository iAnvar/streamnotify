import os
import asyncio
import logging
from telethon import TelegramClient, events
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
from flask import Flask
from waitress import serve

# Настройки логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
try:
    API_ID = int(os.environ.get('TELEGRAM_API_ID', 0))
    API_HASH = os.environ.get('TELEGRAM_API_HASH', '')
    BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    ADMIN_CHAT_ID = int(os.environ.get('ADMIN_CHAT_ID', 0))
except Exception as e:
    logger.error(f"Ошибка при загрузке переменных окружения: {e}")
    API_ID, API_HASH, BOT_TOKEN, ADMIN_CHAT_ID = 0, '', '', 0

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
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        chat_type = update.effective_chat.type
        
        # Расширенное логирование
        logger.info(f"Start command received")
        logger.info(f"Chat ID: {chat_id}")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Chat Type: {chat_type}")
        logger.info(f"Message: {update.message.text}")
        
        await update.message.reply_text(f'Привет! Твой Chat ID: {chat_id}, Тип чата: {chat_type}')
    except Exception as e:
        logger.error(f"Ошибка в команде /start: {e}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Универсальный обработчик сообщений для диагностики"""
    try:
        logger.info(f"Получено сообщение: {update.message.text}")
        logger.info(f"Chat ID: {update.effective_chat.id}")
        logger.info(f"User ID: {update.effective_user.id}")
        
        await update.message.reply_text(f"Вы написали: {update.message.text}")
    except Exception as e:
        logger.error(f"Ошибка в обработчике сообщений: {e}")

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавление канала в список мониторинга"""
    try:
        # Проверка прав администратора
        if update.effective_user.id != ADMIN_CHAT_ID:
            logger.warning(f"Попытка добавить канал неавторизованным пользователем. User ID: {update.effective_user.id}")
            await update.message.reply_text('У вас нет прав для этой команды.')
            return

        if not context.args:
            await update.message.reply_text('Пожалуйста, укажите username канала')
            return

        channel_username = context.args[0]
        MONITORED_CHANNELS.append(channel_username)
        
        logger.info(f"Канал {channel_username} добавлен в список мониторинга")
        
        await update.message.reply_text(f'Канал {channel_username} добавлен в список мониторинга')
    except Exception as e:
        logger.error(f"Ошибка при добавлении канала: {e}")

async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список мониторируемых каналов"""
    try:
        # Проверка прав администратора
        if update.effective_user.id != ADMIN_CHAT_ID:
            logger.warning(f"Попытка просмотра списка каналов неавторизованным пользователем. User ID: {update.effective_user.id}")
            await update.message.reply_text('У вас нет прав для этой команды.')
            return

        if not MONITORED_CHANNELS:
            await update.message.reply_text('Список мониторинга пуст.')
        else:
            channels_list = '\n'.join(MONITORED_CHANNELS)
            await update.message.reply_text(f'Мониторируемые каналы:\n{channels_list}')
    except Exception as e:
        logger.error(f"Ошибка при просмотре списка каналов: {e}")

async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление канала из списка мониторинга"""
    try:
        # Проверка прав администратора
        if update.effective_user.id != ADMIN_CHAT_ID:
            logger.warning(f"Попытка удаления канала неавторизованным пользователем. User ID: {update.effective_user.id}")
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
    except Exception as e:
        logger.error(f"Ошибка при удалении канала: {e}")

async def monitor_streams(application):
    """Мониторинг стримов в указанных каналах"""
    try:
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
                        logger.error(f"Ошибка отправки сообщения о стриме: {e}")
    except Exception as e:
        logger.error(f"Ошибка в мониторинге стримов: {e}")

async def main():
    """Запуск бота"""
    try:
        # Проверка обязательных переменных
        if not all([API_ID, API_HASH, BOT_TOKEN, ADMIN_CHAT_ID]):
            logger.error("Не все обязательные переменные окружения установлены!")
            return

        application = Application.builder().token(BOT_TOKEN).build()

        # Регистрация команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("add_channel", add_channel))
        application.add_handler(CommandHandler("remove_channel", remove_channel))
        application.add_handler(CommandHandler("list_channels", list_channels))
        
        # Универсальный обработчик сообщений для диагностики
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

        # Запуск бота и клиента
        await application.initialize()
        await application.start()
        
        # Запуск мониторинга стримов
        await monitor_streams(application)
        
        await application.updater.start_polling()
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")

# Обновленный запуск для Render
if __name__ == '__main__':
    import threading

    def run_bot():
        asyncio.run(main())

    def run_flask():
        serve(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

    # Запускаем бота и Flask в разных потоках
    bot_thread = threading.Thread(target=run_bot)
    flask_thread = threading.Thread(target=run_flask)

    bot_thread.start()
    flask_thread.start()

    bot_thread.join()
    flask_thread.join()