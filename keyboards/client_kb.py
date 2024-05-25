from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

b1 = KeyboardButton('Заказать пропуск')
b2 = KeyboardButton('Легковой')
b3 = KeyboardButton('Грузовой')
b4 = KeyboardButton('Назад')
b5 = KeyboardButton('Все верно')
b6 = KeyboardButton('Отмена')
b7 = KeyboardButton('Авторизация')
b8 = KeyboardButton('отмена')


client_1 = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1).add(b1)
type_car = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(b2, b3, b4, b6)
back = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(b4, b6)
check = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(b5, b4, b6)
authorization = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1).add(b7)
stop = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1).add(b6)
start_break = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1).add(b8)

