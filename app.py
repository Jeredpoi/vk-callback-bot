
from flask import Flask, request
import json
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import sqlite3
import os

app = Flask(__name__)

# Конфигурация
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

CONFIRMATION_TOKEN = config["confirmation_token"]
GROUP_ID = config["group_id"]
SECRET = config["secret"]
VK_TOKEN = config["vk_token"]

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

DB_PATH = "users.db"

def connect_db():
    return sqlite3.connect(DB_PATH)

def get_user_link(user_id):
    return f"https://vk.com/id{user_id}"

def get_roles(user_id):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT role FROM roles WHERE user_id = ?", (str(user_id),))
        return [row[0] for row in cur.fetchall()]

def has_role(user_id, role):
    return role in get_roles(user_id)

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
        "Команды:\n"
        "/setnick\n"
        "/nicklist\n"
        "/giverole\n"
        "/removerole\n"
        "/help"
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
            if entries:
                text = "📋 Ники:
" + "
".join([f"{uid} → {nick}" for uid, nick in entries])
            else:
                text = "🔍 Ники не найдены"
            vk.messages.send(peer_id=peer_id, message=text, random_id=0)

        elif cmd == "/giverole" and len(args) == 3 and has_role(user_id, "admin"):
            target = args[1].replace("@", "").replace("[", "").replace("]", "")
            role = args[2].lower()
            add_role(target, role)
            vk.messages.send(peer_id=peer_id, message=f"✅ Роль {role} выдана пользователю {target}", random_id=0)

        elif cmd == "/removerole" and len(args) == 2 and has_role(user_id, "admin"):
            target = args[1].replace("@", "").replace("[", "").replace("]", "")
            remove_role(target)
            vk.messages.send(peer_id=peer_id, message=f"❌ Все роли пользователя {target} удалены", random_id=0)

    return "ok"
