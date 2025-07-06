
import json
from utils import send_message, get_role, get_user_link

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def handle_command(user_id, text):
    args = text.strip().split()
    cmd = args[0].lower()
    role = get_role(user_id)

    if cmd == "/help":
        send_message(user_id, "Доступные команды:\n" +
            "/id\n/mynick\n/setnick <ник>\n/nicks\n" +
            ("/mute <@user>\n/clear <N>\n" if role >= 1 else "") +
            ("/ban <@user> <причина>\n/unban <@user>\n/setrole <@user> <0|1|2>\n/roles" if role >= 2 else "")
        )

    elif cmd == "/id":
        send_message(user_id, f"Твоя ссылка: {get_user_link(user_id)}")

    elif cmd == "/setnick" and len(args) > 1:
        nicks = load_json("nicks.json")
        nicks[str(user_id)] = " ".join(args[1:])
        save_json("nicks.json", nicks)
        send_message(user_id, "Ник сохранён.")

    elif cmd == "/mynick":
        nicks = load_json("nicks.json")
        nick = nicks.get(str(user_id), "Не установлен")
        send_message(user_id, f"Твой ник: {nick}")

    elif cmd == "/nicks":
        nicks = load_json("nicks.json")
        if nicks:
            msg = "\n".join([f"{k}: {v}" for k, v in nicks.items()])
            send_message(user_id, msg)
        else:
            send_message(user_id, "Ников нет.")

    elif cmd == "/mute" and role >= 1:
        send_message(user_id, "⛔ Мут выдан (фейк, нужно реализовать мут через фильтрацию сообщений).")

    elif cmd == "/clear" and role >= 1 and len(args) > 1:
        send_message(user_id, f"🧹 Очищено {args[1]} сообщений (визуально, без реального удаления).")

    elif cmd == "/ban" and role >= 2 and len(args) > 1:
        target_id = args[1].replace("@id", "")
        reason = " ".join(args[2:]) if len(args) > 2 else "не указана"
        bans = load_json("bans.json")
        bans[target_id] = reason
        save_json("bans.json", bans)

        keyboard = {
            "inline": True,
            "buttons": [[
                {
                    "action": {
                        "type": "callback",
                        "label": "🔓 Разбанить",
                        "payload": json.dumps({"action": "unban", "target": target_id})
                    }
                },
                {
                    "action": {
                        "type": "callback",
                        "label": "🧹 Очистить сообщения",
                        "payload": json.dumps({"action": "clear_user_msgs", "target": target_id})
                    }
                }
            ]]
        }

        send_message(user_id, f"🚫 {target_id} забанен. Причина: {reason}", keyboard)

    elif cmd == "/unban" and role >= 2 and len(args) > 1:
        target_id = args[1].replace("@id", "")
        bans = load_json("bans.json")
        if target_id in bans:
            del bans[target_id]
            save_json("bans.json", bans)
            send_message(user_id, f"✅ {target_id} разбанен.")
        else:
            send_message(user_id, "Пользователь не в бане.")

    elif cmd == "/setrole" and role >= 2 and len(args) >= 3:
        target_id = args[1].replace("@id", "")
        new_role = int(args[2])
        roles = load_json("roles.json")
        roles[target_id] = new_role
        save_json("roles.json", roles)
        send_message(user_id, f"✅ Установлен уровень доступа {new_role} для {target_id}.")

    elif cmd == "/roles" and role >= 2:
        roles = load_json("roles.json")
        if roles:
            msg = "\n".join([f"{k}: {v}" for k, v in roles.items()])
            send_message(user_id, msg)
        else:
            send_message(user_id, "Нет назначенных ролей.")

    else:
        send_message(user_id, "Неизвестная или недоступная команда.")

def handle_button(user_id, payload):
    action = payload.get("action")
    target = payload.get("target")
    role = get_role(user_id)

    if action == "unban" and role >= 2:
        bans = load_json("bans.json")
        if target in bans:
            del bans[target]
            save_json("bans.json", bans)
            send_message(user_id, f"✅ {target} разбанен.")

    elif action == "clear_user_msgs" and role >= 2:
        send_message(user_id, f"🧹 Сообщения пользователя {target} визуально очищены (заглушка).")

    else:
        send_message(user_id, "Нет доступа или неизвестное действие.")
