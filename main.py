import os
from telethon import TelegramClient, events
from telegram.ext import Application, CommandHandler
import asyncio
import logging

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
MONITORED_CHANNELS = []  # Список каналов для мониторинга

# Клиент для мониторинга стримов
client = TelegramClient('session', API_ID, API_HASH)

# Бот для отправки уведомлений
async def start(update, context):
    """Команда /start для взаимодействия с ботом"""
    await update.message.reply_text('Привет! Я бот для оповещений о стримах.')

async def add_channel(update, context):
    """Добавление канала в список мониторинга"""
    if context.args:
        channel_username = context.args[0]
        MONITORED_CHANNELS.append(channel_username)
        await update.message.reply_text(f'Канал {channel_username} добавлен в список мониторинга')
    else:
        await update.message.reply_text('Пожалуйста, укажите username канала')

async def remove_channel(update, context):
    """Удаление канала из списка мониторинга"""
    if context.args:
        channel_username = context.args[0]
        if channel_username in MONITORED_CHANNELS:
            MONITORED_CHANNELS.remove(channel_username)
            await update.message.reply_text(f'Канал {channel_username} удален из списка мониторинга')
        else:
            await update.message.reply_text('Канал не найден в списке мониторинга')
    else:
        await update.message.reply_text('Пожалуйста, укажите username канала')

async def monitor_streams(application):
    """Мониторинг стримов в указанных каналах"""
    async with client:
        @client.on(events.NewMessage(chats=MONITORED_CHANNELS))
        async def stream_handler(event):
            # Здесь логика определения начала стрима
            # Например, по наличию тега #live или другим признакам
            if '#live' in event.message.text:
                # Отправка уведомления в телеграм-бот
                await application.bot.send_message(
                    chat_id=-1001601477384, 
                    text=f'Начался стрим в канале {event.chat.username}!'
                )

async def main():
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_channel", add_channel))
    application.add_handler(CommandHandler("remove_channel", remove_channel))

    # Запуск бота и клиента
    await application.initialize()
    await application.start()
    
    # Запуск мониторинга стримов
    await monitor_streams(application)
    
    await application.updater.start_polling()
    await application.updater.idle()

if __name__ == '__main__':
    asyncio.run(main())