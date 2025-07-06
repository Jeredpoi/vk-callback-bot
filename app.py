from flask import Flask, request
import json
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import sqlite3
import os
from datetime import datetime, timedelta
import time

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
START_TIME = time.time()

# Подключение к базе
def connect_db():
    return sqlite3.connect(DB_PATH)

def get_user_link(user_id):
    return f"https://vk.com/id{user_id}"

def get_roles(user_id):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT role FROM roles WHERE user_id = ?", (str(user_id),))
        return [row[0] for row in cur.fetchall()]

def has_role(user_id, role, peer_id=None):
    roles = get_roles(user_id)
    if role in roles:
        return True

    if role == "admin" and peer_id:
        try:
            members = vk.messages.getConversationMembers(peer_id=peer_id)["items"]
            for member in members:
                if member["member_id"] == user_id and (
                    member.get("is_admin") or member.get("is_owner")
                ):
                    return True
        except Exception as e:
            print("Ошибка проверки прав администратора чата:", e)

    return False


def set_nick(user_id, nickname):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("REPLACE INTO users (user_id, nickname) VALUES (?, ?)", (str(user_id), nickname))
        conn.commit()

def get_nicklist():
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, nickname FROM users")
        return cur.fetchall()

def add_role(user_id, role):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("REPLACE INTO roles (user_id, role) VALUES (?, ?)", (str(user_id), role))
        conn.commit()

def remove_role(user_id):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM roles WHERE user_id = ?", (str(user_id),))
        conn.commit()

def get_uptime():
    uptime = time.time() - START_TIME
    return str(timedelta(seconds=int(uptime)))

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

        if cmd == "/help":
            vk.messages.send(
                peer_id=peer_id,
                message=(
                    "\U0001F4D8 Команды:\n"
                    "/setnick @user ник — установить ник\n"
                    "/nicklist — список ников\n"
                    "/giverole @user роль — выдать роль\n"
                    "/removerole @user — удалить роль\n"
                    "/addmod @user — выдать модера\n"
                    "/removemod @user — убрать модера\n"
                    "/ping — проверка\n"
                    "/time — время\n"
                    "/uptime — аптайм\n"
                    "/help — помощь"
                ),
                random_id=0
            )

        elif cmd == "/setnick" and len(args) >= 3:
            if has_role(user_id, "moderator") or has_role(user_id, "admin"):
                target = args[1].replace("@", "").replace("[", "").replace("]", "")
                nick = " ".join(args[2:])
                set_nick(target, nick)
                vk.messages.send(peer_id=peer_id, message=f"✅ Ник установлен: {nick}", random_id=0)
            else:
                vk.messages.send(peer_id=peer_id, message="❌ Недостаточно прав", random_id=0)

        elif cmd == "/nicklist":
            entries = get_nicklist()
            text = "📋 Ники:\n" + "\n".join([f"{uid}: {nick}" for uid, nick in entries]) if entries else "❌ Ники не найдены"
            vk.messages.send(peer_id=peer_id, message=text, random_id=0)

        elif cmd == "/giverole" and len(args) >= 3 and has_role(user_id, "admin"):
            target = args[1].replace("@", "").replace("[", "").replace("]", "")
            role = args[2]
            add_role(target, role)
            vk.messages.send(peer_id=peer_id, message=f"✅ Роль {role} выдана", random_id=0)

        elif cmd == "/removerole" and len(args) >= 2 and has_role(user_id, "admin"):
            target = args[1].replace("@", "").replace("[", "").replace("]", "")
            remove_role(target)
            vk.messages.send(peer_id=peer_id, message="✅ Роль удалена", random_id=0)

        elif cmd == "/addmod" and len(args) >= 2 and has_role(user_id, "admin"):
            target = args[1].replace("@", "").replace("[", "").replace("]", "")
            add_role(target, "moderator")
            vk.messages.send(peer_id=peer_id, message="✅ Назначен модератор", random_id=0)

        elif cmd == "/removemod" and len(args) >= 2 and has_role(user_id, "admin"):
            target = args[1].replace("@", "").replace("[", "").replace("]", "")
            remove_role(target)
            vk.messages.send(peer_id=peer_id, message="✅ Модератор снят", random_id=0)

        elif cmd == "/ping":
            vk.messages.send(peer_id=peer_id, message="🏓 Pong!", random_id=0)

        elif cmd == "/time":
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            vk.messages.send(peer_id=peer_id, message=f"⏰ Время сервера: {now}", random_id=0)

        elif cmd == "/uptime":
            vk.messages.send(peer_id=peer_id, message=f"⏳ Аптайм: {get_uptime()}", random_id=0)

        else:
            vk.messages.send(peer_id=peer_id, message="❌ Неизвестная команда или недостаточно аргументов", random_id=0)

    return "ok"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
