import mysql.connector
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import asyncio

TOKEN = "8974791081:AAGu68UhGYWWZXU0IqORQd5MHjRHmUM-lSU"

ADMINS = [8065108309]  # Telegram ID главного администратора

bot = Bot(token=TOKEN)
dp = Dispatcher()

db = mysql.connector.connect(
    host="localhost",
    user="vardyrussia",
    password="vardyrussia",
    database="vardyrussia"
)

@dp.message(Command("start"))
async def start(message: Message):
    if message.from_user.id not in ADMINS:
        return await message.answer("Нет доступа.")
    
    await message.answer(
        "/admins - список\n"
        "/setrank ID Звание\n"
        "/add Ник Звание\n"
        "/del ID"
    )

@dp.message(Command("admins"))
async def admins(message: Message):
    if message.from_user.id not in ADMINS:
        return

    cursor = db.cursor()
    cursor.execute("SELECT id,nickname,rank FROM admins")

    text = "Список администраторов:\n\n"

    for admin in cursor.fetchall():
        text += f"#{admin[0]} | {admin[1]} | {admin[2]}\n"

    await message.answer(text)

@dp.message(Command("setrank"))
async def setrank(message: Message):
    if message.from_user.id not in ADMINS:
        return

    args = message.text.split(maxsplit=2)

    if len(args) < 3:
        return await message.answer(
            "Пример:\n/setrank 5 Главный Администратор"
        )

    admin_id = args[1]
    rank = args[2]

    cursor = db.cursor()
    cursor.execute(
        "UPDATE admins SET rank=%s WHERE id=%s",
        (rank, admin_id)
    )
    db.commit()

    await message.answer("Звание обновлено.")

@dp.message(Command("add"))
async def add_admin(message: Message):
    if message.from_user.id not in ADMINS:
        return

    args = message.text.split(maxsplit=2)

    if len(args) < 3:
        return

    nickname = args[1]
    rank = args[2]

    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO admins (nickname,rank) VALUES (%s,%s)",
        (nickname, rank)
    )
    db.commit()

    await message.answer("Администратор добавлен.")

@dp.message(Command("del"))
async def delete_admin(message: Message):
    if message.from_user.id not in ADMINS:
        return

    args = message.text.split()

    if len(args) < 2:
        return

    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM admins WHERE id=%s",
        (args[1],)
    )
    db.commit()

    await message.answer("Администратор удален.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
