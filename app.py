from flask import Flask, render_template, request
import random
import requests
import os

app = Flask(__name__)

webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

def send_to_discord(username, roll_type, result):
        message = f"🎲 **{username}** rolled **{roll_type}** → **{result}**"
        payload = {"content": message}
        requests.post(webhook_url, json=payload)

@app.route("/", methods=["GET", "POST"])
def index():
        result = None
        username = None
        roll_type = None

        if request.method == "POST":
            roll_type = request.form.get("roll_type")
            username = request.form.get("username", "").strip()

            if username:
                result = "Success" if random.random() < 0.5 else "Fail"
                send_to_discord(username, roll_type, result)

        return render_template("index.html", result=result, username=username, roll_type=roll_type)

if __name__ == "__main__":
        app.run(debug=True)
