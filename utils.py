import json
import requests

ACCESS_TOKEN = "твой_токен"
API_VERSION = "5.199"
VK_API_URL = "https://api.vk.com/method/"

def send_message(user_id, text, keyboard=None):
    payload = {
        "access_token": ACCESS_TOKEN,
        "v": API_VERSION,
        "user_id": user_id,
        "message": text,
        "random_id": 0
    }
    if keyboard:
        payload["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
    requests.post(VK_API_URL + "messages.send", data=payload)

def get_role(user_id):
    try:
        with open("roles.json", "r", encoding="utf-8") as f:
            roles = json.load(f)
        return roles.get(str(user_id), 0)
    except:
        return 0

def get_user_link(user_id):
    return f"https://vk.com/id{user_id}"
