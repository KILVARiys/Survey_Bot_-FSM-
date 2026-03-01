import asyncio
import logging
import json

from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

class FeedBackFromUser(StatesGroup):
    name = State()
    phone = State()
    rating = State()
    comment = State()

TOKEN = 'YOUR_TOKEN'

dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(FeedBackFromUser.name)
    await message.answer(text='Здравствуйте, пройдите опрос\nКак вас зовут?')

@dp.message(FeedBackFromUser.name)
async def proces_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(FeedBackFromUser.phone)
    await message.answer(text='Напишите ваш телефон для связи')

@dp.message(FeedBackFromUser.phone)
async def proces_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(FeedBackFromUser.rating)
    
    rating_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
            [KeyboardButton(text="4"), KeyboardButton(text="5")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "Оцените нашу работу от 1 до 5:",
        reply_markup=rating_keyboard
    )

@dp.message(FeedBackFromUser.rating)
async def proces_rating(message: types.Message, state: FSMContext):
    if message.text not in ["1", "2", "3", "4", "5"]:
        rating_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
                [KeyboardButton(text="4"), KeyboardButton(text="5")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(
            "Пожалуйста, оцените от 1 до 5, используя кнопки ниже:",
            reply_markup=rating_keyboard
        )
        return

    await state.update_data(rating=message.text)
    await state.set_state(FeedBackFromUser.comment)
    await message.answer(
        'Спасибо за оценку! Напишите, пожалуйста, отзыв:',
        reply_markup=types.ReplyKeyboardRemove()
    )

@dp.message(FeedBackFromUser.comment)
async def proces_comment(message: types.Message, state: FSMContext):
    await state.update_data(comment=message.text)
    user_data = await state.get_data()
    
    confirmation_text = (
        "Проверьте введённые данные:\n\n"
        f"Имя: {user_data.get('name')}\n"
        f"Телефон: {user_data.get('phone')}\n"
        f"Оценка: {user_data.get('rating')}\n"
        f"Комментарий: {user_data.get('comment')}\n\n"
        "Всё верно?"
    )
    
    confirm_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, всё верно", callback_data="confirm_yes"),
                InlineKeyboardButton(text="Нет, заполнить заново", callback_data="confirm_no")
            ]
        ]
    )
    
    await message.answer(
        confirmation_text,
        reply_markup=confirm_keyboard
    )

@dp.callback_query(F.data == "confirm_yes")
async def confirm_yes(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()

    # Добавляем мета-информацию
    feedback_entry = {
        'user_id': callback.from_user.id,
        'username': callback.from_user.username,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'data': user_data
    }
    
    filename = 'data.json'

    with open(filename, 'r', encoding='utf-8') as file:
        try:
            all_feedbacks = json.load(file)
        except json.JSONDecodeError:
            all_feedbacks = []

    all_feedbacks.append(feedback_entry)

    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(all_feedbacks, file, ensure_ascii=False, indent=4)
    
    await callback.message.edit_text(
        "Спасибо! Ваш отзыв принят.",
        reply_markup=None
    )
    
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "confirm_no")
async def confirm_no(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(FeedBackFromUser.name)
    
    await callback.message.edit_text(
        "Давайте начнём заново.\nКак вас зовут?"
    )
    await callback.answer()

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
