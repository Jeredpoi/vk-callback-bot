from flask import Flask, request, Response

app = Flask(__name__)

CONFIRMATION_TOKEN = "d897c6fe"  # токен подтверждения из VK
SECRET = "a77ads8ed88aw80dz"          # подставь сюда свой секретный ключ (если используешь)
GROUP_ID = 231458075             # ID твоей группы

@app.route("/", methods=["POST"])
def callback():
    data = request.json

    if data["type"] == "confirmation" and data["group_id"] == GROUP_ID:
        return Response(CONFIRMATION_TOKEN, content_type="text/plain")

    if data["type"] == "message_new":
        print("Новое сообщение:", data["object"]["message"]["text"])

    return "ok"
