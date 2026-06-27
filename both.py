# автор Shumaher
import time
import random
import sqlite3
import json
from datetime import datetime, timedelta
from contextlib import closing
import requests

# --- КОНФИГУРАЦИЯ ---
TOKEN = "88974791081:AAGu68UhGYWWZXU0IqORQd5MHjRHmUM-lSU"
ADMIN_ID = 8065108309
last_update_id = 0

# --- ФУНКЦИИ TELEGRAM ---
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code != 200:
            print(f"Ошибка отправки: {response.text}")
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def send_keyboard(chat_id, text, keyboard):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "reply_markup": json.dumps(keyboard), "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Ошибка: {e}")

def answer_callback(callback_id):
    url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
    data = {"callback_query_id": callback_id}
    try:
        requests.post(url, data=data, timeout=5)
    except:
        pass

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        response = requests.get(url, params=params, timeout=35)
        data = response.json()
        return data.get("result", [])
    except Exception as e:
        print(f"Ошибка получения обновлений: {e}")
        return []

# --- БАЗА ДАННЫХ ---
def init_db():
    with closing(sqlite3.connect('economy_bot.db')) as conn:
        with conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    balance INTEGER DEFAULT 0,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    work TEXT DEFAULT 'Уборщик',
                    last_work_time TIMESTAMP DEFAULT '2000-01-01',
                    house TEXT DEFAULT '',
                    garage TEXT DEFAULT '',
                    business TEXT DEFAULT '',
                    warns INTEGER DEFAULT 0,
                    last_tax_time TIMESTAMP DEFAULT '2000-01-01',
                    event_points INTEGER DEFAULT 0
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    user_id INTEGER,
                    item_name TEXT,
                    quantity INTEGER,
                    PRIMARY KEY (user_id, item_name)
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS bans (
                    user_id INTEGER PRIMARY KEY
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS promocodes (
                    code TEXT PRIMARY KEY,
                    reward INTEGER,
                    uses_left INTEGER
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    description TEXT,
                    task_type TEXT,
                    task_count INTEGER,
                    reward_points INTEGER,
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    active INTEGER DEFAULT 1
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS event_shop (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT,
                    price INTEGER
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS custom_businesses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    price INTEGER,
                    income_min INTEGER,
                    income_max INTEGER,
                    tax INTEGER,
                    level_req INTEGER DEFAULT 1
                )
            ''')
            
            # Добавляем тестовые данные
            try:
                conn.execute("INSERT OR IGNORE INTO event_shop (id, item_name, price) VALUES (1, 'Эксклюзивный скин', 100)")
                conn.execute("INSERT OR IGNORE INTO event_shop (id, item_name, price) VALUES (2, 'Обмен на монеты', 1)")
                conn.execute("INSERT OR IGNORE INTO custom_businesses (id, name, price, income_min, income_max, tax, level_req) VALUES (1, 'Кафе', 5000, 300, 600, 200, 3)")
                conn.execute("INSERT OR IGNORE INTO custom_businesses (id, name, price, income_min, income_max, tax, level_req) VALUES (2, 'Автосервис', 8000, 500, 1000, 300, 5)")
            except:
                pass

init_db()

def get_user(user_id):
    with closing(sqlite3.connect('economy_bot.db')) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            conn.commit()
            return get_user(user_id)
        return user

def update_user(user_id, **kwargs):
    with closing(sqlite3.connect('economy_bot.db')) as conn:
        for key, value in kwargs.items():
            conn.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))
        conn.commit()

def add_item(user_id, item_name):
    with closing(sqlite3.connect('economy_bot.db')) as conn:
        conn.execute("INSERT INTO inventory (user_id, item_name, quantity) VALUES (?, ?, 1) "
                     "ON CONFLICT(user_id, item_name) DO UPDATE SET quantity = quantity + 1",
                     (user_id, item_name))
        conn.commit()

def get_inventory(user_id):
    with closing(sqlite3.connect('economy_bot.db')) as conn:
        cursor = conn.execute("SELECT item_name, quantity FROM inventory WHERE user_id = ?", (user_id,))
        return cursor.fetchall()

def is_banned(user_id):
    with closing(sqlite3.connect('economy_bot.db')) as conn:
        cursor = conn.execute("SELECT 1 FROM bans WHERE user_id = ?", (user_id,))
        return cursor.fetchone() is not None

def get_xp_for_next_level(level):
    if level == 1:
        return 100
    return 100 + (level - 1) * 50

def add_xp(user_id, amount):
    user = get_user(user_id)
    new_xp = user['xp'] + amount
    level = user['level']
    leveled_up = False
    while True:
        need_xp = get_xp_for_next_level(level)
        if new_xp >= need_xp:
            new_xp -= need_xp
            level += 1
            leveled_up = True
        else:
            break
    update_user(user_id, xp=new_xp, level=level)
    return leveled_up, level

WORKS = {
    1: {"name": "Уборщик", "min": 100, "max": 250, "level_req": 1},
    2: {"name": "Шахтер", "min": 250, "max": 750, "level_req": 2},
    3: {"name": "Кассир", "min": 750, "max": 1250, "level_req": 5},
    4: {"name": "Сварщик", "min": 1250, "max": 1750, "level_req": 10},
    5: {"name": "Пилот", "min": 1750, "max": 2500, "level_req": 15},
}

SHOP_ITEMS = {
    "аптечка": 500,
    "билет": 250,
    "энергетик": 150,
    "пицца": 300,
}

# --- ОБРАБОТЧИКИ КОМАНД ---
def handle_start(chat_id):
    text = """👋 *Добро пожаловать!*

📋 *Команды:*
/balance - Баланс
/profile - Профиль
/work - Работать
/rob - Ограбить банк
/steal - Угнать авто
/shop - Магазин
/inventory - Инвентарь
/buyhouse - Купить дом (5000💰)
/buygarage - Купить гараж (3000💰)
/buybusiness - Купить бизнес
/event - Ивент
/eventshop - Ивент магазин
/promo - Промокод
/donate - Донат

⚙️ *Админ:*
/admin - Админ панель"""
    send_message(chat_id, text)

def handle_balance(chat_id, user_id):
    if is_banned(user_id):
        send_message(chat_id, "🚫 Вы забанены!")
        return
    user = get_user(user_id)
    send_message(chat_id, f"💰 *Баланс:* {user['balance']} B-coins")

def handle_profile(chat_id, user_id):
    if is_banned(user_id):
        send_message(chat_id, "🚫 Вы забанены!")
        return
    
    user = get_user(user_id)
    tax = (200 if user['house'] else 0) + (150 if user['garage'] else 0) + (300 if user['business'] else 0)
    
    text = f"""👤 *Профиль*

💰 Баланс: {user['balance']} B-coins
🎯 Ивент очки: {user['event_points']}
📊 Уровень: {user['level']}
⭐️ Опыт: {user['xp']}/{get_xp_for_next_level(user['level'])}
💼 Работа: {user['work']}

🏠 Дом: {user['house'] if user['house'] else '❌'}
🚗 Гараж: {user['garage'] if user['garage'] else '❌'}
🏢 Бизнес: {user['business'] if user['business'] else '❌'}

💰 Налоги: {tax} B-coins/час"""
    send_message(chat_id, text)

def handle_work(chat_id, user_id):
    if is_banned(user_id):
        send_message(chat_id, "🚫 Вы забанены!")
        return
    
    user = get_user(user_id)
    
    last_work = datetime.fromisoformat(user['last_work_time']) if user['last_work_time'] != '2000-01-01' else datetime.min
    if datetime.now() - last_work < timedelta(minutes=10):
        remaining = timedelta(minutes=10) - (datetime.now() - last_work)
        send_message(chat_id, f"⏳ Отдых! Работа через {remaining.seconds // 60} мин.")
        return
    
    # Находим лучшую доступную работу
    work_data = None
    for w in WORKS.values():
        if w['level_req'] <= user['level']:
            work_data = w
    
    if work_data:
        salary = random.randint(work_data['min'], work_data['max'])
        update_user(user_id, balance=user['balance'] + salary, last_work_time=datetime.now().isoformat(), work=work_data['name'])
        
        leveled, new_level = add_xp(user_id, 50)
        
        send_message(chat_id, f"💼 *{work_data['name']}*\n💰 +{salary} B-coins\n⭐️ +50 опыта")
        if leveled:
            send_message(chat_id, f"🎉 Поздравляем! Вы достигли {new_level} уровня!")
    else:
        send_message(chat_id, "❌ Нет доступных работ!")

def handle_rob(chat_id, user_id):
    if is_banned(user_id):
        send_message(chat_id, "🚫 Вы забанены!")
        return
    
    user = get_user(user_id)
    
    if random.random() < 0.5:
        win = random.randint(500, 3000)
        update_user(user_id, balance=user['balance'] + win)
        send_message(chat_id, f"🏦 *Ограбление удалось!*\n+{win} B-coins")
    else:
        lose = random.randint(300, 1500)
        update_user(user_id, balance=max(0, user['balance'] - lose))
        send_message(chat_id, f"🚨 *Ограбление провалилось!*\nШтраф: {lose} B-coins")

def handle_steal(chat_id, user_id):
    if is_banned(user_id):
        send_message(chat_id, "🚫 Вы забанены!")
        return
    
    user = get_user(user_id)
    
    if random.random() < 0.5:
        win = random.randint(300, 2000)
        update_user(user_id, balance=user['balance'] + win)
        send_message(chat_id, f"🚗 *Угон удался!*\n+{win} B-coins")
    else:
        lose = random.randint(200, 1200)
        update_user(user_id, balance=max(0, user['balance'] - lose))
        send_message(chat_id, f"🚨 *Угон не удался!*\nШтраф: {lose} B-coins")

def handle_shop(chat_id, user_id):
    if is_banned(user_id):
        send_message(chat_id, "🚫 Вы забанены!")
        return
    
    keyboard = {"inline_keyboard": []}
    for item, price in SHOP_ITEMS.items():
        keyboard["inline_keyboard"].append([{"text": f"{item} - {price}💰", "callback_data": f"buy_{item}"}])
    keyboard["inline_keyboard"].append([{"text": "❌ Закрыть", "callback_data": "close"}])
    
    send_keyboard(chat_id, "🏪 *Магазин*", keyboard)

def handle_inventory(chat_id, user_id):
    if is_banned(user_id):
        send_message(chat_id, "🚫 Вы забанены!")
        return
    
    items = get_inventory(user_id)
    if items:
        text = "🎒 *Инвентарь:*\n\n"
        for item, qty in items:
            text += f"📦 {item}: {qty} шт.\n"
        send_message(chat_id, text)
    else:
        send_message(chat_id, "🎒 *Инвентарь пуст*")

def handle_buyhouse(chat_id, user_id):
    if is_banned(user_id):
        send_message(chat_id, "🚫 Вы забанены!")
        return
    
    user = get_user(user_id)
    if user['house']:
        send_message(chat_id, "🏠 У вас уже есть дом!")
    elif user['balance'] >= 5000:
        update_user(user_id, balance=user['balance'] - 5000, house="Дом")
        send_message(chat_id, "🏠 *Дом куплен!* -5000 B-coins\n⚠️ Налог: 200/час")
    else:
        send_message(chat_id, "❌ Нужно 5000 B-coins")

def handle_buygarage(chat_id, user_id):
    if is_banned(user_id):
        send_message(chat_id, "🚫 Вы забанены!")
        return
    
    user = get_user(user_id)
    if user['garage']:
        send_message(chat_id, "🚗 У вас уже есть гараж!")
    elif user['balance'] >= 3000:
        update_user(user_id, balance=user['balance'] - 3000, garage="Гараж")
        send_message(chat_id, "🚗 *Гараж куплен!* -3000 B-coins\n⚠️ Налог: 150/час")
    else:
        send_message(chat_id, "❌ Нужно 3000 B-coins")

def handle_buybusiness(chat_id, user_id):
    if is_banned(user_id):
        send_message(chat_id, "🚫 Вы забанены!")
        return
    
    with closing(sqlite3.connect('economy_bot.db')) as conn:
        businesses = conn.execute("SELECT * FROM custom_businesses").fetchall()
        if businesses:
            keyboard = {"inline_keyboard": []}
            for b in businesses:
                keyboard["inline_keyboard"].append([{"text": f"{b[1]} - {b[2]}💰", "callback_data": f"buybiz_{b[0]}"}])
            keyboard["inline_keyboard"].append([{"text": "❌ Закрыть", "callback_data": "close"}])
            send_keyboard(chat_id, "🏢 *Доступные бизнесы*", keyboard)
        else:
            send_message(chat_id, "🏢 *Нет доступных бизнесов*")

def handle_event(chat_id):
    with closing(sqlite3.connect('economy_bot.db')) as conn:
        event = conn.execute("SELECT * FROM events WHERE active = 1").fetchone()
        if event:
            task_ru = "ограбление" if event[3] == "rob" else "угон"
            send_message(chat_id, f"🎯 *{event[1]}*\n\n{event[2]}\n🎯 Задание: {task_ru} {event[4]} раз\n🏆 Награда: {event[5]} очков")
        else:
            send_message(chat_id, "🎯 *Нет активных ивентов*")

def handle_eventshop(chat_id, user_id):
    if is_banned(user_id):
        send_message(chat_id, "🚫 Вы забанены!")
        return
    
    user = get_user(user_id)
    
    with closing(sqlite3.connect('economy_bot.db')) as conn:
        items = conn.execute("SELECT * FROM event_shop").fetchall()
        if items:
            keyboard = {"inline_keyboard": []}
            for item in items:
                if item[1] == "Обмен на монеты":
                    keyboard["inline_keyboard"].append([{"text": f"💱 {item[1]} - {item[2]}🎯", "callback_data": f"exchange"}])
                else:
                    keyboard["inline_keyboard"].append([{"text": f"🛒 {item[1]} - {item[2]}🎯", "callback_data": f"eventbuy_{item[0]}"}])
            keyboard["inline_keyboard"].append([{"text": "❌ Закрыть", "callback_data": "close"}])
            send_keyboard(chat_id, f"🎯 *Ивент магазин*\nУ вас: {user['event_points']} очков\n\n1 очко = 1000 B-coins", keyboard)
        else:
            send_message(chat_id, "🎯 *Магазин пуст*")

def handle_promo(chat_id, user_id):
    if is_banned(user_id):
        send_message(chat_id, "🚫 Вы забанены!")
        return
    
    send_message(chat_id, "📝 *Введите промокод:*")
    # Сохраняем состояние ожидания
    return "waiting_promo"

def handle_promo_input(chat_id, user_id, text):
    code = text.upper()
    with closing(sqlite3.connect('economy_bot.db')) as conn:
        promo = conn.execute("SELECT * FROM promocodes WHERE code = ? AND uses_left > 0", (code,)).fetchone()
        if promo:
            conn.execute("UPDATE promocodes SET uses_left = uses_left - 1 WHERE code = ?", (code,))
            conn.commit()
            user = get_user(user_id)
            update_user(user_id, balance=user['balance'] + promo[1])
            send_message(chat_id, f"✅ *Промокод активирован!*\n+{promo[1]} B-coins")
        else:
            send_message(chat_id, "❌ *Неверный промокод*")

def handle_donate(chat_id):
    send_message(chat_id, f"💎 *Донат меню*\n\n💰 Поддержать проект: @Beluga_KpyT\n\n✨ Задонатив, вы получите:\n• 5000 B-coins\n• 100 ивент очков\n• Эксклюзивный статус\n\n📩 Для получения наград напишите @Beluga_KpyT после доната")

def handle_admin(chat_id, user_id):
    if user_id != ADMIN_ID:
        send_message(chat_id, "❌ Нет прав!")
        return
    
    keyboard = {"inline_keyboard": [
        [{"text": "💰 Выдать деньги", "callback_data": "ad_give"}],
        [{"text": "📢 Рассылка", "callback_data": "ad_broad"}],
        [{"text": "🎁 Создать промокод", "callback_data": "ad_promo"}],
        [{"text": "🎯 Создать ивент", "callback_data": "ad_event"}],
        [{"text": "📊 Статистика", "callback_data": "ad_stats"}]
    ]}
    send_keyboard(chat_id, "⚙️ *Админ панель*", keyboard)

def admin_give(chat_id):
    send_message(chat_id, "📝 Введите ID и сумму: 123456789 1000")
    return "admin_give"

def admin_broadcast(chat_id):
    send_message(chat_id, "📝 Введите текст рассылки:")
    return "admin_broadcast"

def admin_promo(chat_id):
    send_message(chat_id, "📝 Введите промокод и сумму: SUMMER24 500")
    return "admin_promo"

def admin_event(chat_id):
    send_message(chat_id, "📝 Введите название ивента:")
    return "admin_event_name"

def admin_stats(chat_id):
    with closing(sqlite3.connect('economy_bot.db')) as conn:
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        balance = conn.execute("SELECT SUM(balance) FROM users").fetchone()[0] or 0
        points = conn.execute("SELECT SUM(event_points) FROM users").fetchone()[0] or 0
        send_message(chat_id, f"📊 *Статистика*\n\n👥 Пользователей: {users}\n💰 Общий баланс: {balance:,} B-coins\n🎯 Всего очков: {points}")

def handle_admin_input(chat_id, user_id, text, state, event_data):
    if state == "admin_give":
        try:
            uid, amount = map(int, text.split())
            user = get_user(uid)
            update_user(uid, balance=user['balance'] + amount)
            send_message(chat_id, f"✅ Выдано {amount} B-coins пользователю {uid}")
            send_message(uid, f"💰 Администратор выдал вам {amount} B-coins!")
        except Exception as e:
            send_message(chat_id, f"❌ Ошибка! Формат: ID сумма\n{str(e)}")
        return None, None
    
    elif state == "admin_broadcast":
        with closing(sqlite3.connect('economy_bot.db')) as conn:
            users = conn.execute("SELECT user_id FROM users").fetchall()
            count = 0
            for (uid,) in users:
                try:
                    send_message(uid, f"📢 *Рассылка*\n\n{text}")
                    count += 1
                    time.sleep(0.05)
                except:
                    pass
        send_message(chat_id, f"✅ Отправлено {count} пользователям")
        return None, None
    
    elif state == "admin_promo":
        try:
            parts = text.split()
            if len(parts) < 2:
                send_message(chat_id, "❌ Ошибка! Формат: КОД СУММА")
                return None, None
            code = parts[0].upper()
            reward = int(parts[1])
            with closing(sqlite3.connect('economy_bot.db')) as conn:
                conn.execute("INSERT INTO promocodes (code, reward, uses_left) VALUES (?, ?, 100)", (code, reward))
                conn.commit()
            send_message(chat_id, f"✅ Промокод {code} создан! Награда: {reward} B-coins")
        except Exception as e:
            send_message(chat_id, f"❌ Ошибка! Формат: КОД СУММА\n{str(e)}")
        return None, None
    
    elif state == "admin_event_name":
        # Сохраняем имя ивента
        return "admin_event_desc", {"name": text}
    
    elif state == "admin_event_desc":
        if not event_data:
            event_data = {}
        event_data['desc'] = text
        send_message(chat_id, "📝 Введите тип ивента (rob или steal):")
        return "admin_event_type", event_data
    
    elif state == "admin_event_type":
        if text.lower() not in ['rob', 'steal']:
            send_message(chat_id, "❌ Типы: rob или steal")
            return "admin_event_type", event_data
        event_data['type'] = text.lower()
        send_message(chat_id, "📝 Введите количество раз:")
        return "admin_event_count", event_data
    
    elif state == "admin_event_count":
        try:
            event_data['count'] = int(text)
            send_message(chat_id, "📝 Введите награду в очках:")
            return "admin_event_reward", event_data
        except:
            send_message(chat_id, "❌ Введите число!")
            return "admin_event_count", event_data
    
    elif state == "admin_event_reward":
        try:
            start = datetime.now()
            end = start + timedelta(days=7)
            with closing(sqlite3.connect('economy_bot.db')) as conn:
                conn.execute("INSERT INTO events (name, description, task_type, task_count, reward_points, start_date, end_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (event_data['name'], event_data['desc'], event_data['type'], event_data['count'], int(text), start.isoformat(), end.isoformat()))
                conn.commit()
            send_message(chat_id, f"✅ Ивент создан!\n{event_data['name']}\nЗадание: {event_data['type']} {event_data['count']} раз\nНаграда: {text} очков")
        except Exception as e:
            send_message(chat_id, f"❌ Ошибка!\n{str(e)}")
        return None, None
    
    return state, event_data

# --- ОБРАБОТКА КНОПОК ---
def handle_callback(chat_id, message_id, user_id, data):
    # Покупка в магазине
    if data.startswith("buy_"):
        item = data.split("_")[1]
        if item in SHOP_ITEMS:
            user = get_user(user_id)
            price = SHOP_ITEMS[item]
            if user['balance'] >= price:
                update_user(user_id, balance=user['balance'] - price)
                add_item(user_id, item)
                send_message(chat_id, f"✅ *Куплено:* {item}\n💰 -{price} B-coins")
            else:
                send_message(chat_id, f"❌ Нужно {price} B-coins")
    
    # Покупка бизнеса
    elif data.startswith("buybiz_"):
        biz_id = int(data.split("_")[1])
        with closing(sqlite3.connect('economy_bot.db')) as conn:
            biz = conn.execute("SELECT * FROM custom_businesses WHERE id = ?", (biz_id,)).fetchone()
            if biz:
                user = get_user(user_id)
                if user['business']:
                    send_message(chat_id, "🏢 У вас уже есть бизнес!")
                elif user['level'] < biz[6]:
                    send_message(chat_id, f"❌ Нужен {biz[6]} уровень!")
                elif user['balance'] >= biz[2]:
                    update_user(user_id, balance=user['balance'] - biz[2], business=biz[1])
                    send_message(chat_id, f"🏢 *{biz[1]} куплен!*\n💰 -{biz[2]} B-coins\n💼 Доход: {biz[3]}-{biz[4]} B-coins/час\n⚠️ Налог: {biz[5]} B-coins/час")
                else:
                    send_message(chat_id, f"❌ Нужно {biz[2]} B-coins")
    
    # Обмен очков
    elif data == "exchange":
        user = get_user(user_id)
        if user['event_points'] > 0:
            coins = user['event_points'] * 1000
            update_user(user_id, event_points=0, balance=user['balance'] + coins)
            send_message(chat_id, f"💱 *Обмен выполнен!*\n🎯 -{user['event_points']} очков\n💰 +{coins} B-coins")
        else:
            send_message(chat_id, "❌ У вас нет очков!")
    
    # Покупка в ивент магазине
    elif data.startswith("eventbuy_"):
        item_id = int(data.split("_")[1])
        with closing(sqlite3.connect('economy_bot.db')) as conn:
            item = conn.execute("SELECT * FROM event_shop WHERE id = ?", (item_id,)).fetchone()
            if item:
                user = get_user(user_id)
                if user['event_points'] >= item[2]:
                    update_user(user_id, event_points=user['event_points'] - item[2])
                    add_item(user_id, item[1])
                    send_message(chat_id, f"✅ *Куплено:* {item[1]}!\n🎯 -{item[2]} очков")
                else:
                    send_message(chat_id, f"❌ Нужно {item[2]} очков!")
    
    # Админ кнопки
    elif data.startswith("ad_"):
        if user_id != ADMIN_ID:
            send_message(chat_id, "❌ Нет прав!")
            return
        
        action = data.split("_")[1]
        if action == "give":
            state = admin_give(chat_id)
            user_states[user_id] = state
            user_event_data[user_id] = None
        elif action == "broad":
            state = admin_broadcast(chat_id)
            user_states[user_id] = state
            user_event_data[user_id] = None
        elif action == "promo":
            state = admin_promo(chat_id)
            user_states[user_id] = state
            user_event_data[user_id] = None
        elif action == "event":
            state = admin_event(chat_id)
            user_states[user_id] = state
            user_event_data[user_id] = {}
        elif action == "stats":
            admin_stats(chat_id)
    
    elif data == "close":
        pass

# --- ОСНОВНОЙ ЦИКЛ ---
user_states = {}
user_event_data = {}

def main():
    global last_update_id
    print("=" * 50)
    print("🤖 БОТ ЗАПУЩЕН!")
    print("✅ Команды: /start, /balance, /work, /profile")
    print("=" * 50)
    
    while True:
        try:
            updates = get_updates(last_update_id + 1 if last_update_id else None)
            
            for update in updates:
                last_update_id = update.get("update_id")
                
                # Обработка сообщений
                if "message" in update:
                    msg = update["message"]
                    chat_id = msg["chat"]["id"]
                    user_id = msg["from"]["id"]
                    text = msg.get("text", "")
                    
                    print(f"Получено сообщение: {text} от {user_id}")
                    
                    if is_banned(user_id):
                        continue
                    
                    # Обработка состояний
                    if user_id in user_states:
                        state = user_states[user_id]
                        event_data = user_event_data.get(user_id, {})
                        
                        if state.startswith("admin_"):
                            new_state, new_data = handle_admin_input(chat_id, user_id, text, state, event_data)
                            if new_state is None:
                                del user_states[user_id]
                                if user_id in user_event_data:
                                    del user_event_data[user_id]
                            else:
                                user_states[user_id] = new_state
                                if new_data is not None:
                                    user_event_data[user_id] = new_data
                        elif state == "waiting_promo":
                            handle_promo_input(chat_id, user_id, text)
                            del user_states[user_id]
                        continue
                    
                    # Обработка команд (только если нет активного состояния)
                    if text == "/start":
                        handle_start(chat_id)
                    elif text == "/balance":
                        handle_balance(chat_id, user_id)
                    elif text == "/profile":
                        handle_profile(chat_id, user_id)
                    elif text == "/work":
                        handle_work(chat_id, user_id)
                    elif text == "/rob":
                        handle_rob(chat_id, user_id)
                    elif text == "/steal":
                        handle_steal(chat_id, user_id)
                    elif text == "/shop":
                        handle_shop(chat_id, user_id)
                    elif text == "/inventory":
                        handle_inventory(chat_id, user_id)
                    elif text == "/buyhouse":
                        handle_buyhouse(chat_id, user_id)
                    elif text == "/buygarage":
                        handle_buygarage(chat_id, user_id)
                    elif text == "/buybusiness":
                        handle_buybusiness(chat_id, user_id)
                    elif text == "/event":
                        handle_event(chat_id)
                    elif text == "/eventshop":
                        handle_eventshop(chat_id, user_id)
                    elif text == "/promo":
                        state = handle_promo(chat_id, user_id)
                        if state:
                            user_states[user_id] = state
                    elif text == "/donate":
                        handle_donate(chat_id)
                    elif text == "/admin":
                        handle_admin(chat_id, user_id)
                    elif text.startswith("/"):
                        send_message(chat_id, "❌ Неизвестная команда\nИспользуйте /start")
                
                # Обработка кнопок
                if "callback_query" in update:
                    cb = update["callback_query"]
                    chat_id = cb["message"]["chat"]["id"]
                    message_id = cb["message"]["message_id"]
                    user_id = cb["from"]["id"]
                    data = cb["data"]
                    handle_callback(chat_id, message_id, user_id, data)
                    answer_callback(cb["id"])
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Ошибка: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)

if __name__ == "__main__":
    main()    rows = cursor.fetchall()

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
