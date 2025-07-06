from flask import Flask, request, Response
import json
from utils import get_role, send_message, get_user_link
from handlers import handle_command, handle_button

app = Flask(__name__)
CONFIRMATION_TOKEN = "d897c6fe"
ACCESS_TOKEN = "твой_токен"
GROUP_ID = 231458075
API_VERSION = "5.199"

@app.route("/", methods=["POST"])
def vk_callback():
    data = request.json

    if data["type"] == "confirmation":
        return Response(CONFIRMATION_TOKEN, content_type="text/plain")

    if data["type"] == "message_new":
        msg = data["object"]["message"]
        user_id = msg["from_id"]
        text = msg["text"]
        payload = msg.get("payload")

        if payload:
            handle_button(user_id, json.loads(payload))
        else:
            handle_command(user_id, text)

    return "ok"
