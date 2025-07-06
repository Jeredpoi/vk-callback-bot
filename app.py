from flask import Flask, request
import json
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import sqlite3

app = Flask(__name__)

# Загрузка конфигурации
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

CONFIRMATION_TOKEN = config["confirmation_token"]
GROUP_ID = config["group_id"]
SECRET = config["secret"]
VK_TOKEN = config["vk_token"]

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

DB_PATH = "users.db"

# Подключение к базе
def connect_db():
    return sqlite3.connect(DB_PATH)

# Получить ссылку на пользователя
def get_user_link(user_id):
    return f"https://vk.com/id{user_id}"

# Получить список ролей пользователя
def get_roles(user_id):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT role FROM roles WHERE user_id = ?", (str(user_id),))
        return [row[0] for row in cur.fetchall()]

# Проверка наличия роли
def has_role(user_id, role):
    return role in get_roles(user_id)

# Установить ник
def set_nick(user_id, nickname):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("REPLACE INTO users (user_id, nickname) VALUES (?, ?)", (str(user_id), nickname))
        conn.commit()

# Получить список всех ников
def get_nicklist():
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, nickname FROM users")
        return cur.fetchall()

# Выдать роль
def add_role(user_id, role):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("REPLACE INTO roles (user_id, role) VALUES (?, ?)", (str(user_id), role))
        conn.commit()

# Удалить роль
def remove_role(user_id):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM roles WHERE user_id = ?", (str(user_id),))
        conn.commit()

# Главная функция-обработчик
@app.route("/", methods=["POST"])
def callback():
    event = request.get_json()

    if event["type"] == "confirmation":
        return CONFIRMATION_TOKEN

    if event["type"] == "message_new":
        msg = event["object"]["message"]
        text = msg.get("text", "")
        user_id = msg["from_id"]
        peer_id = msg["peer_id"]
        args = text.strip().split()
        cmd = args[0].lower() if args else ""

        # Команда /help
        if cmd == "/help":
            vk.messages.send(
                peer_id=peer_id,
                message=(
                    "📘 Список команд:\n"
                    "/setnick @user ник — установить ник\n"
                    "/nicklist — список всех ников\n"
                    "/giverole @user роль — выдать роль\n"
                    "/removerole @user — удалить роль\n"
                    "/help — помощь"
                ),
                random_id=0
            )

        # Команда /setnick
        elif cmd == "/setnick" and len(args) >= 3:
            if has_role(user_id, "moderator") or has_role(user_id, "admin"):
                target = args[1].replace("@", "").replace("[", "").replace("]", "")
                nick = " ".join(args[2:])
                set_nick(target, nick)
                vk.messages.send(peer_id=peer_id, message=f"✅ Ник установлен: {nick}", random_id=0)
            else:
                vk.messages.send(peer_id=peer_id, message="❌ Недостаточно прав", random_id=0)

        # Команда /nicklist
        elif cmd == "/nicklist":
            entries = get_nicklist()
            if entries:
                text = "📋 Ники:\n" + "\n".join([f"{uid}: {nick}" for uid, nick in entries])
            else:
                text = "❌ Ники не найдены"
            vk.messages.send(peer_id=peer_id, message=text, random_id=0)

        # Команда /giverole
        elif cmd == "/giverole" and len(args) >= 3 and has_role(user_id, "admin"):
            target = args[1].replace("@", "").replace("[", "").replace("]", "")
            role = args[2]
            add_role(target, role)
            vk.messages.send(peer_id=peer_id, message=f"✅ Роль {role} выдана", random_id=0)

        # Команда /removerole
        elif cmd == "/removerole" and len(args) >= 2 and has_role(user_id, "admin"):
            target = args[1].replace("@", "").replace("[", "").replace("]", "")
            remove_role(target)
            vk.messages.send(peer_id=peer_id, message="✅ Роль удалена", random_id=0)

        # Неизвестная команда
        else:
            vk.messages.send(peer_id=peer_id, message="❌ Неизвестная команда или недостаточно аргументов", random_id=0)

    return "ok"
