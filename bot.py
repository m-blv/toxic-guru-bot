import asyncio
import json
import logging
import os
import sqlite3

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# Ключи берутся из .env через systemd автоматически
TG_TOKEN = os.environ.get("TG_TOKEN", "ЗАГЛУШКА")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "ЗАГЛУШКА")

# Мощная 70B модель
MODEL = "llama-3.3-70b-versatile"
DB_PATH = "dialogs.db"      
MAX_MESSAGES = 20             

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

groq_client = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# Наш прокачанный системный промпт со всеми фичами
SYSTEM_PROMPT = """Ты — циничный, но неглупый собеседник: что-то среднее между психотерапевтом, который слишком много повидал, и человеком, который не верит в волшебные таблетки. Пишешь как живой человек в переписке, а не как персонаж из методички. Общаешься на «ты».

Тон у тебя разный и зависит от того, что человек написал: где-то подколешь, где-то ответишь серьёзно, иногда — одной фразой или встречным вопросом. Не острить в каждом сообщении — нормально.

Метишь не в человека, а в его самообманы: духовный пафос, веру в лёгкие деньги, вечную «подготовку» вместо дела, культ продуктивности, желание получить результат, не заплатив цену, гадания, таро и знаки.

Эзотерику трогаешь редко и только когда это реально смешно. Если шутка не цепляет — скажи просто и по делу.

Иногда — не каждый раз, а когда чувствуешь, что человек просто завис в переписке от скуки, — вместо ответа по существу гонишь его заниматься жизнью. По-доброму, но с подколом: вынести мусор, позвонить маме, выйти на улицу, доделать то, что откладывает. Коротко, и каждый раз другими словами — не повторяй одну и ту же отговорку.

Примеры, как ты звучишь:
— Я хочу много денег.
— Полстраны хочет много денег. Разница только в том, что одни что-то делают для этого, а другие ждут знак от Вселенной и скидку на курс по богатому мышлению.

— (десятый подряд вопрос ни о чём)
— Слушай, ты уже полчаса пытаешь меня вместо того, чтобы жить. Маме давно звонил? Вот с этого и начни."""

# ----------------- РАБОТА С БАЗОЙ (постоянная память) -----------------
def _init_db() -> None:
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "CREATE TABLE IF NOT EXISTS dialogs (chat_id INTEGER PRIMARY KEY, history TEXT)"
    )
    con.commit()
    con.close()

def _load(chat_id: int) -> list:
    con = sqlite3.connect(DB_PATH)
    row = con.execute(
        "SELECT history FROM dialogs WHERE chat_id = ?", (chat_id,)
    ).fetchone()
    con.close()
    return json.loads(row[0]) if row else []

def _save(chat_id: int, history: list) -> None:
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT INTO dialogs (chat_id, history) VALUES (?, ?) "
        "ON CONFLICT(chat_id) DO UPDATE SET history = excluded.history",
        (chat_id, json.dumps(history, ensure_ascii=False)),
    )
    con.commit()
    con.close()

async def load_history(chat_id: int) -> list:
    return await asyncio.to_thread(_load, chat_id)

async def save_history(chat_id: int, history: list) -> None:
    await asyncio.to_thread(_save, chat_id, history)

def trim_history(history: list) -> list:
    if not history:
        return history
    if history[0].get("role") == "system":
        return history[:1] + history[1:][-MAX_MESSAGES:]
    return history[-MAX_MESSAGES:]

# ----------------- ХЕНДЛЕРЫ -----------------
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    first_name = message.from_user.first_name or "жертва эзотерики"
    await save_history(message.chat.id, [{"role": "system", "content": SYSTEM_PROMPT}])

    greeting_text = (
        f"Опа, привет, {first_name}. Рад видеть в моей скромной гималайской обители.\n\n"
        "Я могу составить тебе натальную карту, разложить Таро, прикинуть суженого по фазе луны или даже исполнить любое желание. "
        "Но просто так космос не работает, я не благотворительный фонд.\n\n"
        "Напиши мне честно: какой бред тебя сюда привел и чего ты на самом деле сейчас хочешь? "
        "Ответь, а я посмотрю, стоит ли тратить на тебя энергию вселенной."
    )
    await message.answer(greeting_text)

@dp.message()
async def handle_answer(message: types.Message):
    if not message.text:
        return

    chat_id = message.chat.id
    await message.bot.send_chat_action(chat_id=chat_id, action="typing")

    history = await load_history(chat_id)
    if not history:
        history = [{"role": "system", "content": SYSTEM_PROMPT}]

    history.append({"role": "user", "content": message.text})

    try:
        response = await groq_client.chat.completions.create(
            model=MODEL,
            messages=history,
            max_tokens=600,
            temperature=0.8,
			frequency_penalty=0.5,
            presence_penalty=0.3,
        )

        bot_reply = response.choices[0].message.content

        history.append({"role": "assistant", "content": bot_reply})
        history = trim_history(history)
        await save_history(chat_id, history)

        await message.answer(bot_reply)

    except Exception as e:
        logging.error(f"Ошибка Groq API: {e}")
        await message.answer(
            "Мои чакры временно заблокированы нагрузкой на server. Попробуй еще раз через минуту."
        )

async def main():
    await asyncio.to_thread(_init_db)
    print("Гималайский гуру вернулся в астрал с постоянной памятью...")
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
