from flask import Flask, render_template, request
import random
import requests
import os

app = Flask(__name__)

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1395671663265452062/Vx_J6VzEXJp6AO7KSnjXU6gn1WIVzd3zMTv0ks4j7Wy8ZSncuq1pxdEAW0-rGWJQ1aoH"  # Replace with your actual webhook

def send_to_discord(username, roll_type, result):
        message = f"🎲 **{username}** rolled **{roll_type}** → **{result}**"
        payload = {"content": message}
        requests.post(DISCORD_WEBHOOK_URL, json=payload)

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