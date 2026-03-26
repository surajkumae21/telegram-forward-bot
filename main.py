import os
from telethon import TelegramClient

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

client = TelegramClient("session", API_ID, API_HASH)

async def main():
    print("Userbot started successfully")
    await client.start()
    await client.run_until_disconnected()

client.loop.run_until_complete(main())
