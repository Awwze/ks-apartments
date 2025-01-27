import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Определение состояний для ConversationHandler
MAIN_MENU, GET_PHOTOS, GET_DESCRIPTION, GET_CONTACT = range(4)

# Идентификатор вашего канала для уведомлений
channel_id = '@ks_apartments'  # Замените на ваш идентификатор канала

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [['📸 Опубликовать', '🤝 Сотрудничество']]
    await update.message.reply_text(
        'Добро пожаловать! Выберите действие:',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return MAIN_MENU

async def publish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [['Назад']]
    await update.message.reply_text(
        'Пожалуйста, отправьте минимум 3 фото вашего дома или квартиры.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    context.user_data['photos'] = []
    return GET_PHOTOS

async def get_photos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == 'Назад':
        return await start(update, context)
    if update.message.photo:
        context.user_data['photos'].append(update.message.photo[-1].file_id)
        if len(context.user_data['photos']) >= 3:
            await update.message.reply_text('Теперь отправьте описание вашего дома или квартиры.')
            return GET_DESCRIPTION
        else:
            await update.message.reply_text('Пожалуйста, отправьте еще фото.')
            return GET_PHOTOS
    else:
        await update.message.reply_text('Пожалуйста, отправьте фото.')
        return GET_PHOTOS

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == 'Назад':
        return await start(update, context)
    context.user_data['description'] = update.message.text
    reply_keyboard = [[KeyboardButton("Отправить номер телефона", request_contact=True)], ['Назад']]
    await update.message.reply_text(
        'Пожалуйста, отправьте ваш номер телефона, используя кнопку ниже.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return GET_CONTACT

async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == 'Назад':
        return await start(update, context)
    if update.message.contact:
        context.user_data['phone_number'] = update.message.contact.phone_number
        context.user_data['username'] = update.message.from_user.username
        await update.message.reply_text('Спасибо! Ваше объявление отправлено на модерацию.', reply_markup=ReplyKeyboardRemove())

        media_group = []
        for i, photo in enumerate(context.user_data['photos']):
            caption = (
                f"{context.user_data['description']}\n"
                f"Номер телефона: {context.user_data['phone_number']}\n"
                f"Юзернейм: @{context.user_data['username']}\n"
                f"❗️Сервис не несет ответственность за Ваши сделки❗️"
            )
            media_group.append(InputMediaPhoto(photo, caption=caption if i == 0 else ""))

        await context.bot.send_media_group(chat_id=channel_id, media=media_group)

        context.user_data.clear()
        return await start(update, context)  # Возвращаем пользователя в главное меню после публикации
    else:
        await update.message.reply_text('Пожалуйста, используйте кнопку ниже для отправки номера телефона.')
        return GET_CONTACT

async def cooperation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Для сотрудничества, пожалуйста, свяжитесь с нами по почте - connect.dev.studio@gmail.com или напишите в телеграм - @tgAkbarr.')
    return MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('До свидания! Надеемся увидеть вас снова.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token("7112513940:AAGd6zzA4-NO9MjY8VrWo8ZC7_mkV_fx8i4").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.Regex('^(📸 Опубликовать)$'), publish),
                MessageHandler(filters.Regex('^(🤝 Сотрудничество)$'), cooperation),
            ],
            GET_PHOTOS: [
                MessageHandler(filters.PHOTO, get_photos),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_photos),
            ],
            GET_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)
            ],
            GET_CONTACT: [
                MessageHandler(filters.CONTACT, get_contact),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()