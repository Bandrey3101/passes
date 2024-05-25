import datetime
from aiogram import types, Bot, executor, Dispatcher
from telegram_bot_calendar import WMonthTelegramCalendar
import config
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery
from aiogram.dispatcher.filters.state import State, StatesGroup
from keyboards import client_kb
from data_base import sql_pk
from keyboards import admin_kb
import logging

logging.basicConfig(filename='errors.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

import asyncio

# Инициализация бота и диспетчера
bot = Bot(token=config.token)
dp = Dispatcher(bot, storage=MemoryStorage())

today = datetime.date.today().strftime('%d.%m.%Y')
tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%d.%m.%Y')


class FSMclient(StatesGroup):
    car_type = State()
    brand = State()
    car_number = State()
    check = State()
    check_number = State()


user_data = {}


# @dp.message_handler(commands=['start', 'help'])
async def command_start(message: types.Message):
    await bot.send_message(message.chat.id, 'Здравствуйте, для использования бота необходимо авторизоваться:',
                           reply_markup=client_kb.authorization)


async def cancel_hand2(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data.clear()
    current_state = await state.get_state()
    if current_state is None:
        await command_start(message)
    else:
        await state.finish()
        await command_start(message)


async def cancel_hand(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data.clear()
    current_state = await state.get_state()
    if current_state is None:
        await bot.send_message(message.from_user.id, "Заявка отменена", reply_markup=client_kb.client_1)
    else:
        await state.finish()
        await bot.send_message(message.from_user.id, "Заявка отменена", reply_markup=client_kb.client_1)


async def authorization(message: types.Message):
    await bot.send_message(message.chat.id, 'Для авторизации, введите ваш номер телефона в формате '
                                            '89121231212', reply_markup=client_kb.start_break)
    await FSMclient.check_number.set()


async def check_number(message: types.Message, state: FSMContext):
    row = await sql_pk.search_phone_number(message.text.strip())
    if row:
        await bot.send_message(message.from_user.id, "Авторизация прошла успешно", reply_markup=client_kb.client_1)
        await sql_pk.add_user_id(message.from_user.id, message.text.strip())
        await state.finish()
    else:
        await message.answer('Номер телефона не найден в базе данных, проверьте номер или обратитесь к администратору',
                             reply_markup=client_kb.start_break)


async def new_pass(message: types.Message, state: FSMContext):
    try:
        row = await sql_pk.search_user_id(message.from_user.id)
        if row is None:
            await bot.send_message(message.from_user.id, "Воспользуйтесь командой /start",
                                   reply_markup=client_kb.client_1)
        else:
            async with state.proxy() as data:
                print(row[0], '1')
                print(row[1], '2')
                data['company'] = row[0]
                data['phone'] = row[1]
                data['user_id'] = message.from_user.id
            keyboard = InlineKeyboardMarkup(row_width=1)
            buttons = [
                InlineKeyboardButton(text=f"Сегодня {datetime.date.today().strftime('%d.%m.%Y')}",
                                     callback_data="today"),
                InlineKeyboardButton(
                    text=f"Завтра {(datetime.date.today() + datetime.timedelta(days=1)).strftime('%d.%m.%Y')}",
                    callback_data="tomorrow"),
                InlineKeyboardButton(text="Выбор даты", callback_data="another")
            ]
            keyboard.add(*buttons)
            await message.answer("На какую дату выдать пропуск?", reply_markup=keyboard)
    except Exception as e:
        data.clear()
        await state.finish()
        logging.error("Номера нет в БД: %s", str(e))
        await bot.send_message(message.from_user.id, "Воспользуйтесь командой /start", reply_markup=client_kb.client_1)


async def back(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await bot.send_message(message.from_user.id, 'Главное меню', reply_markup=client_kb.client_1)
    elif current_state == FSMclient.car_type.state:
        await state.finish()
        await new_pass(message, state)
    elif current_state == FSMclient.brand.state:
        await FSMclient.car_type.set()
        await bot.send_message(message.from_user.id, "Выберите вид ТС:", reply_markup=client_kb.type_car)
    elif current_state == FSMclient.car_number.state:
        await FSMclient.brand.set()
        await bot.send_message(message.from_user.id, "Напишите марку авто:", reply_markup=client_kb.back)
    elif current_state == FSMclient.check.state:
        await FSMclient.car_number.set()
        await bot.send_message(message.from_user.id, "Напишите гос номер авто в формате 777"
                                                     "(без букв и региона):", reply_markup=client_kb.back)


# @dp.callback_query_handler(lambda c: c.data == 'another')
async def start_calendar(c: CallbackQuery):
    calendarbot, step = WMonthTelegramCalendar(locale='ru', min_date=datetime.date.today(),
                                               max_date=datetime.date.today() + datetime.timedelta(days=60)).build()
    await bot.send_message(c.message.chat.id, "Выберите день", reply_markup=calendarbot)


@dp.callback_query_handler(WMonthTelegramCalendar.func())
async def process_calendar_selection(c: CallbackQuery, state: FSMContext):
    result, key, step = WMonthTelegramCalendar(locale='ru', min_date=datetime.date.today(),
                                               max_date=datetime.date.today() + datetime.timedelta(days=60)).process(
        c.data)
    if not result and key:
        await bot.edit_message_text("Выберите день", c.message.chat.id, c.message.message_id,
                                    reply_markup=key)
    elif result:
        async with state.proxy() as data:
            data['date'] = result
        await FSMclient.car_type.set()
        await bot.edit_message_text(f"Вы выбрали: {result.strftime('%d.%m.%Y')}", c.message.chat.id,
                                    c.message.message_id)
        await bot.send_message(c.message.chat.id, "Выберите вид ТС:", reply_markup=client_kb.type_car)


# @dp.callback_query_handler(lambda c: c.data in ["today", "tomorrow"])
async def process_callback_button(c: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        if c.data == "today":
            data['date'] = datetime.date.today()
        elif c.data == "tomorrow":
            data['date'] = datetime.date.today() + datetime.timedelta(days=1)
    await FSMclient.car_type.set()
    await bot.answer_callback_query(c.id)
    await bot.send_message(c.message.chat.id, "Выберите вид ТС:", reply_markup=client_kb.type_car)


# @dp.message_handler(state=FSMclient.car_type)
async def get_car(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['car_type'] = message.text
    await FSMclient.brand.set()
    await bot.send_message(message.from_user.id, "Напишите марку авто:", reply_markup=client_kb.back)


# @dp.message_handler(state=FSMclient.brand)
async def get_car_brand(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['brand'] = message.text
    await FSMclient.car_number.set()
    await bot.send_message(message.from_user.id, "Напишите гос номер авто в формате 777 "
                                                 "(без букв и региона):", reply_markup=client_kb.back)


# @dp.message_handler(state=FSMclient.brand)
async def get_car_number(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['car_number'] = message.text
        await bot.send_message(message.chat.id,
                               f'Проверяем:\n\nКомпания: {data["company"]}\n'
                               f'Дата: {data["date"].strftime("%d.%m.%Y")}\n'
                               f'Вид ТС: {data["car_type"]} \n'
                               f'Марка ТС: {data["brand"]}\n'
                               f'Гос. номер: {data["car_number"]}\n\n'
                               f'Все верно?', reply_markup=client_kb.check)
    await FSMclient.check.set()


async def check(message: types.Message, state: FSMContext):
    try:
        if message.text == "Все верно":
            async with state.proxy() as data:
                data['status'] = 'Анкета отправлена'
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                buttons = [
                    types.InlineKeyboardButton(text=f"Запрос отклонен", callback_data="pass Запрос отклонен"),
                    types.InlineKeyboardButton(text=f"Пропуск выписан", callback_data="pass Пропуск выписан"),
                ]
                keyboard.add(*buttons)
                # Отправляем сообщение с инлайн-кнопками
                sent_message = await bot.send_message(chat_id=config.ID, text=f'Заявка на пропуск.\n'
                                                                              f'Компания: {data["company"]}\n'
                                                                              f'Заказчик: {data["phone"]}\n'
                                                                              f'Дата: {data["date"].strftime("%d.%m.%Y")}\n'
                                                                              f'Вид ТС: {data["car_type"]} \n'
                                                                              f'Марка ТС: {data["brand"]}\n'
                                                                              f'Гос. номер: {data["car_number"]}',
                                                      reply_markup=keyboard)
                await sql_pk.sql_add_pass(data)
                # Сохраняем данные о чате и сообщении
                user_data[sent_message.message_id] = {
                    'chat_id': message.chat.id,
                    'message_id': sent_message.message_id
                }
                # Очищаем данные в состоянии
                data.clear()
            await state.finish()
            if config.ID is None:
                await bot.send_message(message.from_user.id, 'Администратор не авторизован',
                                       reply_markup=client_kb.client_1)
            else:
                await bot.send_message(message.from_user.id, 'Заявка на пропуск отправлена. '
                                                             'После обработки заявки вы получите уведомление. Ожидайте.',
                                       reply_markup=client_kb.client_1)
    except Exception as e:
        data.clear()
        await state.finish()
        logging.error("Ошибка в отправке анкеты: %s", str(e))
        await bot.send_message(message.from_user.id, "Что-то пошло не так, проверьте введенные "
                                                     "данные и повторите еще раз", reply_markup=client_kb.client_1)


async def pass_callback_query(callback_query: types.CallbackQuery):
    # Получаем данные о чате из словаря по идентификатору сообщения
    if callback_query.message.message_id in user_data:
        chat_id = user_data[callback_query.message.message_id]['chat_id']
        # Отправляем результат обратно в чат, из которого было отправлено сообщение
        await bot.send_message(chat_id, f"{callback_query.data.replace('pass ', '')}")
        await callback_query.answer(text=f"{callback_query.data.replace('pass ', '')}", show_alert=True)
        await sql_pk.sql_update_status(status=f"{callback_query.data.replace('pass ', '')}", user_id=chat_id)
        button_text = callback_query.data.replace('pass ', '')
        new_button_text = f"☑️ {button_text}"
        new_keyboard = types.InlineKeyboardMarkup(row_width=1)
        new_buttons = [
            types.InlineKeyboardButton(text=new_button_text, callback_data=callback_query.data)
        ]
        new_keyboard.add(*new_buttons)
        await bot.edit_message_reply_markup(chat_id=config.ID, message_id=callback_query.message.message_id,
                                            reply_markup=new_keyboard)


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start', 'help'])
    dp.register_message_handler(cancel_hand, state="*", text='Отмена')
    dp.register_message_handler(cancel_hand2, state="*", text='отмена')
    dp.register_message_handler(authorization, text='Авторизация')
    dp.register_message_handler(new_pass, text='Заказать пропуск')
    dp.register_message_handler(back, state="*", text='Назад')
    dp.register_message_handler(check_number, state=FSMclient.check_number)
    dp.register_callback_query_handler(start_calendar, (lambda c: c.data == 'another'))
    dp.register_callback_query_handler(process_calendar_selection, WMonthTelegramCalendar.func())
    dp.register_callback_query_handler(process_callback_button, (lambda c: c.data in ["today", "tomorrow"]))
    dp.register_callback_query_handler(pass_callback_query, (lambda x: x.data and x.data.startswith('pass ')))
    dp.register_message_handler(get_car, state=FSMclient.car_type)
    dp.register_message_handler(get_car_brand, state=FSMclient.brand)
    dp.register_message_handler(get_car_number, state=FSMclient.car_number)
    dp.register_message_handler(check, state=FSMclient.check)
