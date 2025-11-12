import os
import discord
from keep_alive import keep_alive
from divination import fortune_telling   # ← 匯入占卜副程式

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == "吉占卜":
        await fortune_telling(message)

    elif message.content.startswith('$hello'):
        await message.channel.send('Hello!')

try:
    token = os.getenv("TOKEN") or ""
    if token == "":
        raise Exception("Please add your token to the Secrets pane.")
    keep_alive()
    client.run(token)
except discord.HTTPException as e:
    if e.status == 429:
        print("The Discord servers denied the connection for making too many requests")
        print("See: https://stackoverflow.com/questions/66724687")
    else:
        raise e
