from flask import Flask, render_template, request
import time
import random
import os
import sqlite3
# import discord
# import asyncio
# from threading import Thread

# ─── Flask Setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)

# ─── Discord Bot Setup (Disabled) ──────────────────────────────────────────────
# intents = discord.Intents.default()
# client = discord.Client(intents=intents)
# DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 1234567890))  # Replace later
# DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
# bot_ready = asyncio.Event()

# @client.event
# async def on_ready():
#     print(f"✅ Logged in as {client.user}")
#     bot_ready.set()

# def send_to_discord(username, roll_type, result):
#     message = f"🎲 **{username}** rolled **{roll_type}** → **{result}**"

#     async def send():
#         await bot_ready.wait()
#         channel = client.get_channel(DISCORD_CHANNEL_ID)
#         if channel:
#             await channel.send(message)
#         else:
#             print("❌ Could not find Discord channel.")

#     asyncio.run_coroutine_threadsafe(send(), client.loop)

# ─── Odds System ────────────────────────────────────────────────────────────────
def get_user_odds(username, roll_type):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT attack_odds, defend_odds FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        if roll_type.lower() == 'attack':
            return float(row[0])
        elif roll_type.lower() == 'defend':
            return float(row[1])
    return None

def update_odds(username, roll_type, delta=0.05):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    column = "attack_odds" if roll_type.lower() == "attack" else "defend_odds"
    cursor.execute(f"""
        UPDATE users
        SET {column} = MIN({column} + ?, 0.95)
        WHERE username = ?
    """, (delta, username))

    conn.commit()
    conn.close()

# ─── Flask Routes ──────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    username = None
    roll_type = None

    if request.method == "POST":
        roll_type = request.form.get("roll_type")
        username = request.form.get("username", "").strip()

        if username:
            odds = get_user_odds(username, roll_type)
            if odds is None:
                result = "User not found or invalid roll type"
            else:
                result = "Success" if random.random() < odds else "Fail"
                if result == "Success":
                    update_odds(username, roll_type)
                # send_to_discord(username, roll_type, result)

    return render_template("index.html", result=result, username=username, roll_type=roll_type)

# ─── Run Flask Only (Discord Bot Disabled) ─────────────────────────────────────
if __name__ == "__main__":
    # Thread(target=run_bot).start()
    app.run(debug=True)
