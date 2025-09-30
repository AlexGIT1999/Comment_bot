import logging
import json
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка конфигурации
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

BOT_TOKEN = config['bot_token']
CHANNEL_ID = config['channel_id']
RULES_TEXT = config['rules_text']

# Словарь для отслеживания обработанных групп медиа
processed_media_groups = {}

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает посты из канала и добавляет комментарий с правилами"""
    try:
        message = update.message
        
        # Проверяем, что сообщение от системного аккаунта 777000 и sender_chat наш канал
        if (message.from_user and 
            message.from_user.id == 777000 and 
            hasattr(message, 'sender_chat') and 
            message.sender_chat and 
            message.sender_chat.id == CHANNEL_ID):
            
            # Получаем ID группы медиа (если есть) или ID сообщения
            media_group_id = getattr(message, 'media_group_id', None)
            if media_group_id:
                # Это часть альбома медиа
                post_key = f"media_group_{media_group_id}"
            else:
                # Одиночное сообщение
                if hasattr(message, 'forward_from_message_id'):
                    post_key = f"post_{message.forward_from_message_id}"
                else:
                    post_key = f"msg_{message.message_id}"
            
            logger.info(f"Обнаружен пост. Ключ: {post_key}, ID медиа-группы: {media_group_id}")
            
            # Проверяем, не обрабатывали ли мы уже этот пост/альбом
            if post_key not in processed_media_groups:
                logger.info(f"✅ Новый пост/альбом! Добавляем правила...")
                
                # Отправляем ответ на этот пост (комментарий) с HTML разметкой
                rules_message = await message.reply_text(
                    RULES_TEXT, 
                    parse_mode='HTML'
                )
                
                # Закрепляем наш комментарий
                await context.bot.pin_chat_message(
                    chat_id=message.chat.id,
                    message_id=rules_message.message_id,
                    disable_notification=True
                )
                
                # Помечаем пост как обработанный
                processed_media_groups[post_key] = True
                logger.info(f"✅ Комментарий с правилами добавлен для {post_key}!")
                
                # Ограничиваем размер словаря
                if len(processed_media_groups) > 1000:
                    oldest_key = next(iter(processed_media_groups))
                    del processed_media_groups[oldest_key]
            else:
                logger.info(f"⏩ Пост {post_key} уже обработан, пропускаем...")
            
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")

def main():
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.ALL, handle_channel_post))
    
    logger.info("🤖 Бот запущен!")
    logger.info("📝 Опубликуйте пост в канале для тестирования...")
    application.run_polling()

if __name__ == "__main__":
    main()