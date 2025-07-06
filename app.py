from flask import Flask, request

app = Flask(__name__)

CONFIRMATION_TOKEN = "d897c6fe"  # заменишь на свой
SECRET = "секрет_из_вк"
GROUP_ID = 231458075

@app.route("/", methods=["POST"])
def callback():
    data = request.json

    if data["type"] == "confirmation" and data["group_id"] == GROUP_ID:
        return CONFIRMATION_TOKEN

    if data["type"] == "message_new":
        # Пример простой реакции на сообщение
        print("Новое сообщение:", data["object"]["message"]["text"])

    return "ok"
