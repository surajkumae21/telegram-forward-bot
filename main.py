import os
import json
import asyncio
from telethon import TelegramClient, events
from datetime import datetime, timedelta

# ================= ENV VARIABLES =================

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
OWNER_ID = int(os.getenv("OWNER_ID"))

CONFIG_FILE = "config.json"
USERS_FILE = "users.json"

client = TelegramClient("session", API_ID, API_HASH)


# ================= LOAD DATA =================

def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)


def load_users():
    try:
        with open(USERS_FILE) as f:
            return json.load(f)
    except:
        return {}


def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=2)


config = load_config()
users = load_users()


# ================= SUBSCRIPTION CHECK =================

def is_active(uid):

    if uid not in users:
        return False

    expiry = datetime.fromisoformat(users[uid]["expiry"])

    return expiry > datetime.now()


# ================= APPLY HEADER / FOOTER =================

def format_text(uid, text):

    header = users[uid].get("header", "")
    footer = users[uid].get("footer", "")

    return f"{header}\n\n{text}\n\n{footer}"


# ================= ASSIGN TRIAL =================

def assign_trial(uid):

    trial_days = config["trial_days"]

    expiry = datetime.now() + timedelta(days=trial_days)

    users[uid] = {

        "plan": "trial",
        "sources": [],
        "destinations": [],
        "expiry": expiry.isoformat(),
        "interval": config["default_interval"]

    }

    save_users(users)


# ================= AUTO FORWARD ENGINE =================

@client.on(events.NewMessage)
async def forwarder(event):

    if not event.is_channel:
        return

    source = event.chat.username

    if not source:
        return

    message = event.message.text or event.message.caption

    if not message:
        return

    for uid in users:

        if not is_active(uid):
            continue

        if source in users[uid]["sources"]:

            final_text = format_text(uid, message)

            for dest in users[uid]["destinations"]:

                try:
                    await client.send_message(dest, final_text)
                except:
                    pass


# ================= USER COMMANDS =================

@client.on(events.NewMessage(pattern="/start"))
async def start(event):

    uid = str(event.sender_id)

    if uid not in users:

        assign_trial(uid)

        await event.reply("🎁 Trial activated for 7 days")

    else:

        await event.reply("Bot already active")


@client.on(events.NewMessage(pattern="/add_source"))
async def add_source(event):

    uid = str(event.sender_id)

    if not is_active(uid):
        return

    parts = event.text.split()

    if len(parts) < 2:
        return

    source = parts[1].replace("@", "")

    users[uid]["sources"].append(source)

    save_users(users)

    await event.reply("Source added successfully")


@client.on(events.NewMessage(pattern="/set_dest"))
async def set_dest(event):

    uid = str(event.sender_id)

    if not is_active(uid):
        return

    parts = event.text.split()

    if len(parts) < 2:
        return

    dest = parts[1]

    users[uid]["destinations"].append(dest)

    save_users(users)

    await event.reply("Destination added successfully")


# ================= ADMIN COMMAND =================

@client.on(events.NewMessage(pattern="/stats"))
async def stats(event):

    if event.sender_id != OWNER_ID:
        return

    total = len(users)

    active = sum(1 for u in users if is_active(u))

    expired = total - active

    await event.reply(

        f"📊 Bot Stats\n\n"
        f"Total Users: {total}\n"
        f"Active Users: {active}\n"
        f"Expired Users: {expired}"

    )


# ================= MAIN START =================

async def main():

    print("Bot running on Render successfully")

    await client.start()

    await client.run_until_disconnected()


asyncio.run(main())
