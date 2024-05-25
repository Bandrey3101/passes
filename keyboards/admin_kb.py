from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


b1 = KeyboardButton('Список арендаторов')
b2 = KeyboardButton('Отчет')
b3 = KeyboardButton('Добавить номер телефона')
b4 = KeyboardButton('Удалить номер телефона')
b5 = KeyboardButton('Добавить арендатора')
#b6 = KeyboardButton('отмена')
b7 = KeyboardButton('Пропуск выписан')
b8 = KeyboardButton('Запрос отклонен')
b9 = KeyboardButton('Выход')
b10 = KeyboardButton('Главное меню')


admin_1 = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(b1, b5, b3, b4, b2, b9)
list_company = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(b10, b9)
# back_adm = ReplyKeyboardMarkup(resize_keyboard=True).add(b6)
# button_case_admin = ReplyKeyboardMarkup(resize_keyboard=True).add(button_load, button_delete, b7, b5)
# break_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(button_remove)
# button_case_admin2 = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(b1, b2, b3, b4, b5, b6, button_remove)
passes = ReplyKeyboardMarkup(resize_keyboard=True,  row_width=1).add(b7, b8)
