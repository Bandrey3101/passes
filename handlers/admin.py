from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram import types, Dispatcher
from create_bot import dp, bot
from data_base import sql_pk
from keyboards import admin_kb, client_kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
from telegram_bot_calendar import WMonthTelegramCalendar
import datetime
import logging


logging.basicConfig(filename='errors.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class FSMAdmin(StatesGroup):
    company = State()
    new_number = State()
    del_phone = State()
    start_date = State()
    end_date = State()


async def password(message: types.Message):
    config.ID = message.from_user.id
    await bot.send_message(message.from_user.id, 'Вы вошли в режим администратора',
                           reply_markup=admin_kb.admin_1)


async def admin_exit(message: types.Message):
    await bot.send_message(message.from_user.id, "Вы вышли из режима администратора", reply_markup=client_kb.client_1)


async def list_company(message: types.Message):
    if message.from_user.id == config.ID:
        await bot.send_message(message.from_user.id, 'Список арендаторов:', reply_markup=admin_kb.list_company)
        await sql_pk.sql_list_company(message)


async def cancel_handler(message: types.Message, state: FSMContext):
    if message.from_user.id == config.ID:
        current_state = await state.get_state()
        if current_state is None:
            await password(message)
        else:
            await state.finish()
            await password(message)


async def report(message: types.Message):
    if message.from_user.id == config.ID:
        await bot.send_message(message.from_user.id, "Введите дату начала отчета в формате 22.02.2022",
                               reply_markup=admin_kb.list_company)
        await FSMAdmin.start_date.set()


async def start_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        date_obj = datetime.datetime.strptime(message.text, "%d.%m.%Y")
        data['start'] = date_obj.strftime("%Y-%m-%d")
    await FSMAdmin.end_date.set()
    await bot.send_message(message.from_user.id, "Введите дату окончания отчета в формате 22.02.2022",
                           reply_markup=admin_kb.list_company)


async def end_date(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            date_obj = datetime.datetime.strptime(message.text, "%d.%m.%Y")
            data['end'] = date_obj.strftime("%Y-%m-%d")
            await sql_pk.sql_excel(message.chat.id, "Пропуск выписан", data['start'], data['end'])
            data.clear()
        await state.finish()
    except Exception as e:
        logging.error("Ошибка в отправке отчета: %s", str(e))
        await bot.send_message(message.from_user.id, "Что-то пошло не так, проверьте введенные "
                                                     "данные и повторите еще раз", reply_markup=admin_kb.admin_1)




#     # Создаем календарь для выбора начальной даты отчета
#     start_calendar, _ = WMonthTelegramCalendar(locale='ru', min_date=datetime.date.today(),
#                                                 max_date=datetime.date.today() - datetime.timedelta(days=1100)).build()
#     await bot.send_message(message.chat.id, "Выберите день начала отчета", reply_markup=start_calendar)
#
#
# @dp.callback_query_handler(lambda c: c.data.startswith('start_report'))
# async def process_start_date_selection(c):
#     result, key, _ = WMonthTelegramCalendar(locale='ru', min_date=datetime.date.today(),
#                                             max_date=datetime.date.today() - datetime.timedelta(days=1100)).process(c.data)
#     if not result and key:
#         await bot.edit_message_text("Выберите день начала отчета", c.message.chat.id, c.message.message_id,
#                                     reply_markup=key)
#     elif result:
#         global start_date
#         start_date = result
#         await bot.edit_message_text(f"Вы выбрали: {result.strftime('%d.%m.%Y')}", c.message.chat.id,
#                                     c.message.message_id)
#         # После выбора начальной даты отчета, отправляем календарь для выбора конечной даты
#         end_calendar, _ = WMonthTelegramCalendar(locale='ru', min_date=start_date,
#                                                   max_date=datetime.date.today() - datetime.timedelta(days=1100)).build()
#         await bot.send_message(c.message.chat.id, "Выберите день окончания отчета", reply_markup=end_calendar)
#
#
# @dp.callback_query_handler(lambda c: c.data.startswith('end_report'))
# async def process_end_date_selection(c):
#     result, key, _ = WMonthTelegramCalendar(locale='ru', min_date=datetime.date.today(),
#                                             max_date=datetime.date.today() - datetime.timedelta(days=1100)).process(c.data)
#     if not result and key:
#         await bot.edit_message_text("Выберите день окончания отчета", c.message.chat.id, c.message.message_id,
#                                     reply_markup=key)
#     elif result:
#         global end_date
#         end_date = result
#         await sql_pk.sql_excel(c.message.message_id, "Пропуск выписан")


# text Добавить номер телефона
async def add_phone_number(message: types.Message):
    if message.from_user.id == config.ID:
        keyboard = InlineKeyboardMarkup(row_width=1)
        for i in await sql_pk.sql_list_company2():
            print(i[0])
            button = InlineKeyboardButton(text=i[0], callback_data=f'value_{i[0]}')
            keyboard.add(button)
        await bot.send_message(message.from_user.id, "Выберите компанию, в которую надо добавить номер телефона:",
                               reply_markup=keyboard)


async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    company = callback_query.data.split('_')[1]
    await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id,
                                text=f"Вы выбрали: {company}")
    await bot.send_message(callback_query.from_user.id, "Введите номер телефона в формате 89121231212:",
                           reply_markup=admin_kb.list_company)
    async with state.proxy() as data:
        data['company'] = company
    await FSMAdmin.new_number.set()


async def save_number(message: types.Message, state: FSMContext):
    try:
        if message.from_user.id == config.ID:
            async with state.proxy() as data:
                data['phone'] = message.text
                await sql_pk.sql_add_person(data['company'], data['phone'], '-')
                await state.finish()
                data.clear()
            await bot.send_message(message.from_user.id, 'Номер телефона добавлен', reply_markup=admin_kb.admin_1)
    except Exception as e:
        logging.error("Ошибка в добавлении номера: %s", str(e))
        await bot.send_message(message.from_user.id, "Что-то пошло не так, проверьте введенные "
                                                     "данные и повторите еще раз", reply_markup=admin_kb.admin_1)



# text удалить номер
async def get_number_for_del(message: types.Message):
    if message.from_user.id == config.ID:
        await bot.send_message(message.from_user.id, "Введите номер телефона, который необходимо удалить,"
                                                     " в формате 89121231212:", reply_markup=admin_kb.list_company)
        await FSMAdmin.del_phone.set()


async def del_number(message: types.Message, state: FSMContext):
    try:
        number = message.text.strip()
        await sql_pk.sql_del_person(number)
        await state.finish()
        await bot.send_message(message.from_user.id, 'Номер удален', reply_markup=admin_kb.admin_1)
    except Exception as e:
        logging.error("Ошибка в удалении номера: %s", str(e))
        await bot.send_message(message.from_user.id, "Что-то пошло не так, проверьте введенные "
                                                     "данные и повторите еще раз", reply_markup=admin_kb.admin_1)



# async def del_person(callback_query: types.CallbackQuery, message: types.Message):
#     if message.from_user.id == ID:
#
#         await sql_pk.sql_del_person(callback_query.data.replace('delt ', ''))
#         await callback_query.answer(text=f'Номер {callback_query.data.replace("delt ", "")} удален.', show_alert=True)

# text Добавить арендатора
async def add_company(message: types.Message):
    if message.from_user.id == config.ID:
        await bot.send_message(message.from_user.id, 'Введите название компании:', reply_markup=admin_kb.list_company)
        await FSMAdmin.company.set()


async def save_company(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['new company'] = message.text.strip()
        await sql_pk.sql_add_company(data['new company'])
        await bot.send_message(message.from_user.id, f'Арендатор {data["new company"]} добавлен',
                               reply_markup=admin_kb.admin_1)
        data.clear()
    await state.finish()


async def del_company(callback_query: types.CallbackQuery):
    await sql_pk.sql_del_company(callback_query.data.replace('del ', ''))
    await callback_query.answer(text=f'Арендатор {callback_query.data.replace("del ", "")} удален.', show_alert=True)


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(password, commands='password')
    dp.register_message_handler(cancel_handler, state="*", text='Главное меню')
    dp.register_message_handler(admin_exit, text='Выход')
    dp.register_callback_query_handler(del_company, (lambda x: x.data and x.data.startswith('del ')))
    dp.register_message_handler(list_company, text="Список арендаторов")
    dp.register_message_handler(report, text="Отчет")
    dp.register_message_handler(add_company, text="Добавить арендатора")
    dp.register_message_handler(start_date, state=FSMAdmin.start_date)
    dp.register_message_handler(end_date, state=FSMAdmin.end_date)
    dp.register_message_handler(save_company, state=FSMAdmin.company)
    dp.register_message_handler(save_number, state=FSMAdmin.new_number)
    dp.register_callback_query_handler(process_callback, lambda query: query.data.startswith('value_'))
    dp.register_message_handler(add_phone_number, text="Добавить номер телефона")
    dp.register_message_handler(get_number_for_del, text="Удалить номер телефона")
    dp.register_message_handler(del_number, state=FSMAdmin.del_phone)
    # dp.register_callback_query_handler(del_person, (lambda x: x.data and x.data.startswith('delt ')))
