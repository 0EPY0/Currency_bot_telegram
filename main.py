import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.types import CallbackQuery
from aiogram.filters import Command
z
from parse_pair import convert_currency_erapi

class BotState:
    def __init__(self, bot):
        self.bot = bot
        self.selected_currency_pair = None
        self.layout_template = [
            [
                [
                    types.InlineKeyboardButton(text="RUB/USD", callback_data="RUB/USD"),
                    types.InlineKeyboardButton(text="RUB/EUR", callback_data="RUB/EUR"),
                    types.InlineKeyboardButton(text="RUB/CNY", callback_data="RUB/CNY")
                ],
                [
                    types.InlineKeyboardButton(text="Сменить набор", callback_data="change")
                ]
            ],
            [
                [
                    types.InlineKeyboardButton(text="USD/RUB", callback_data="USD/RUB"),
                    types.InlineKeyboardButton(text="EUR/RUB", callback_data="EUR/RUB"),
                    types.InlineKeyboardButton(text="CNY/RUB", callback_data="CNY/RUB")
                ],
                [
                    types.InlineKeyboardButton(text="Сменить набор", callback_data="change")
                ]
            ]
        ]
        self.layout_index = 0

    async def converter(self, currency_pair, amount):
        # last_updated_datetime = f"{amount} {currency_pair.split('/')[0]} = {amount * 2} {currency_pair.split('/')[1]}"
        # exchange_rates = f"{amount} {currency_pair.split('/')[0]} = {amount * 2} {currency_pair.split('/')[1]}"
        
        currency_pair = currency_pair.split('/')
        last_updated_datetime, exchange_rates = convert_currency_erapi(currency_pair[0], currency_pair[1], amount)
        last_updated_datetime = (f"Last updated datetime: {last_updated_datetime}")
        exchange_rates = f"{amount} {currency_pair[0]} = {exchange_rates} {currency_pair[1]}"
        
        return last_updated_datetime, exchange_rates

dp = Dispatcher()

@dp.message(Command('start', 'restart'))
async def command_start(message: types.Message) -> None:
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=bot_state.layout_template[0])
    bot_state.layout_index = 0
    bot_state.selected_currency_pair = None
    await message.answer(f"Привет, {message.from_user.full_name}! Выбери валюту", reply_markup=keyboard)
    
@dp.message(Command('help'))
async def help_message(message: types.Message):
    help_text = "Данный бот поможет вам с конвертацией самых популярных валют.\n" \
                "Вот некоторые доступные команды:\n" \
                "/restart - Перезапустить бота\n" \
                "/help - Показать это справочное сообщение"
    await message.answer(help_text)


@dp.message(lambda message: bot_state.selected_currency_pair is None or not Command('start', 'restart'))
async def process_amount(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=bot_state.layout_template[bot_state.layout_index])
    await message.answer(f"Выбери валюту:", reply_markup=keyboard)
        

@dp.callback_query(lambda query: query.data == "change")
async def change_buttons_callback(query: CallbackQuery):
    bot_state.layout_index = (bot_state.layout_index + 1) % len(bot_state.layout_template)
    await query.message.edit_reply_markup(reply_markup=types.InlineKeyboardMarkup(inline_keyboard=bot_state.layout_template[bot_state.layout_index]))

@dp.callback_query(lambda query: query.data == "change_amount")
async def change_amount_callback(query: CallbackQuery):
    await query.message.answer("Введите сумму:")
    await query.answer()

@dp.callback_query(lambda query: query.data == "change_currency")
async def change_currency_callback(query: CallbackQuery):
    bot_state.layout_index = (bot_state.layout_index + 1) % len(bot_state.layout_template)
    await query.message.edit_reply_markup(reply_markup=types.InlineKeyboardMarkup(inline_keyboard=bot_state.layout_template[bot_state.layout_index]))
    await query.answer()

@dp.callback_query(lambda query: query.data.split('/')[0] in ["RUB", "USD", "EUR", "CNY"])
async def select_currency_pair(query: CallbackQuery):
    bot_state.selected_currency_pair = query.data
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [   types.InlineKeyboardButton(text="Изменить валюту", callback_data="change_currency_2"),
                types.InlineKeyboardButton(text="Отмена", callback_data="cancel")
            ]
        ])
    await query.message.answer(f"Валютная пара {bot_state.selected_currency_pair}\nВведите сумму", reply_markup=keyboard)
    
    #await query.message.answer(f"Валютная пара {bot_state.selected_currency_pair}\nВведите сумму")
    await query.answer()
    
@dp.callback_query(lambda query: query.data == "change_currency_2" or query.data == "cancel")
async def change_currency_callback(query: CallbackQuery):
    await query.message.edit_reply_markup(reply_markup=types.InlineKeyboardMarkup(inline_keyboard=bot_state.layout_template[bot_state.layout_index]))
    await query.answer()

@dp.message(lambda message: bot_state.selected_currency_pair is not None)
async def process_amount(message: types.Message):
    try:
        amount = float(message.text)
        last_updated_datetime, exchange_rates = await bot_state.converter(bot_state.selected_currency_pair, amount)
        await message.answer(f'{last_updated_datetime}\n{exchange_rates}')
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [   types.InlineKeyboardButton(text="Изменить валюту", callback_data="change_currency_2"),
                types.InlineKeyboardButton(text="Отмена", callback_data="cancel")
            ]
        ])
        await message.answer("Введите новую сумму или поменяйте валюту:", reply_markup=keyboard)
    
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")

async def main():
    
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    Token = ''
    bot = Bot(Token)
    bot_state = BotState(bot)
    asyncio.run(main())
