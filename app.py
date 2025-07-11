import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import sqlite3
import json
from datetime import datetime
import time

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

VK_TOKEN = config["vk_token"]
GROUP_ID = config["group_id"]

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

DB_PATH = "users.db"
start_time = datetime.now()

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

def get_uptime():
    return str(datetime.now() - start_time).split('.')[0]

print("🤖 Бот запущен!")

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        text = event.text
        user_id = event.user_id
        peer_id = event.peer_id
        args = text.strip().split()
        cmd = args[0].lower() if args else ""

        if cmd == "/help":
            vk.messages.send(peer_id=peer_id, message=(
                "\nКоманды:\n"
                "/setnick @id Ник\n"
                "/nicklist\n"
                "/giverole @id роль\n"
                "/removerole @id\n"
                "/id\n"
                "/ban @id\n"
                "/unban @id\n"
                "/ping\n"
                "/uptime\n"
                "/time\n"
                "/help\n"
            ), random_id=0)

        elif cmd == "/setnick" and len(args) >= 3:
            if has_role(user_id, "moderator") or has_role(user_id, "admin"):
                target = args[1].replace("@", "").replace("[", "").replace("]", "")
                nick = " ".join(args[2:])
                set_nick(target, nick)
                vk.messages.send(peer_id=peer_id, message=f"✅ Ник установлен: {nick}", random_id=0)
            else:
                vk.messages.send(peer_id=peer_id, message="❌ Недостаточно прав", random_id=0)

        elif cmd == "/nicklist":
            nicks = get_nicklist()
            text = "\n".join([f"{uid} — {nick}" for uid, nick in nicks]) or "Список пуст"
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

        elif cmd == "/id":
            vk.messages.send(peer_id=peer_id, message=f"🔗 {get_user_link(user_id)}", random_id=0)

        elif cmd == "/ban" and len(args) >= 2 and has_role(user_id, "moderator"):
            target = args[1].replace("@", "").replace("[", "").replace("]", "")
            vk.messages.send(peer_id=peer_id, message=f"⛔ Пользователь {target} забанен.", random_id=0)

        elif cmd == "/unban" and len(args) >= 2 and has_role(user_id, "moderator"):
            target = args[1].replace("@", "").replace("[", "").replace("]", "")
            vk.messages.send(peer_id=peer_id, message=f"✅ Пользователь {target} разбанен.", random_id=0)

        elif cmd == "/ping":
            vk.messages.send(peer_id=peer_id, message="🏓 Pong!", random_id=0)

        elif cmd == "/uptime":
            vk.messages.send(peer_id=peer_id, message=f"⏱ Бот работает: {get_uptime()}", random_id=0)

        elif cmd == "/time":
            now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            vk.messages.send(peer_id=peer_id, message=f"🕒 Текущее время: {now}", random_id=0)

        else:
            vk.messages.send(peer_id=peer_id, message="❌ Неизвестная команда или недостаточно прав", random_id=0)
