import asyncio
import mysql.connector

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

TOKEN = "8974791081:AAGu68UhGYWWZXU0IqORQd5MHjRHmUM-lSU"

ADMINS = [8065108309]

db = mysql.connector.connect(
    host="92.255.104.90",
    port=3311,
    user="vardyrussia",
    password="vardyrussia",
    database="vardyrussia"
)

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("Нет доступа")
        return

    await message.answer(
        "/admins - список админов\n"
        "/setrank ID Звание"
    )


@dp.message(Command("admins"))
async def admins(message: Message):
    if message.from_user.id not in ADMINS:
        return

    cursor = db.cursor()
    cursor.execute("SELECT id, nickname, rank FROM admins")

    rows = cursor.fetchall()

    if not rows:
        await message.answer("Список пуст")
        return

    text = "Администраторы:\n\n"

    for admin in rows:
        text += f"#{admin[0]} | {admin[1]} | {admin[2]}\n"

    await message.answer(text)


@dp.message(Command("setrank"))
async def setrank(message: Message):
    if message.from_user.id not in ADMINS:
        return

    args = message.text.split(maxsplit=2)

    if len(args) < 3:
        await message.answer(
            "Пример:\n/setrank 1 Главный Администратор"
        )
        return

    admin_id = args[1]
    rank = args[2]

    cursor = db.cursor()

    cursor.execute(
        "UPDATE admins SET rank=%s WHERE id=%s",
        (rank, admin_id)
    )

    db.commit()

    await message.answer("Звание изменено")


async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())    await message.answer(
        "Команды:\n"
        "/admins\n"
        "/setrank ID Звание"
    )


@dp.message(Command("admins"))
async def admins(message: Message):
    if message.from_user.id not in ADMINS:
        return

    cursor = db.cursor()
    cursor.execute("SELECT id,nickname,rank FROM admins")

    rows = cursor.fetchall()

    if not rows:
        return await message.answer("Администраторов нет")

    text = ""

    for admin in rows:
        text += f"{admin[0]} | {admin[1]} | {admin[2]}\n"

    await message.answer(text)


async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())        return

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
