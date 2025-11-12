import os
import discord
from keep_alive import keep_alive
from divination import fortune_telling

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

# ✅ 把啟動區塊包起來，避免重複執行
if __name__ == "__main__":
    try:
        token = os.getenv("TOKEN") or ""
        if token == "":
            raise Exception("Please add your token to the Secrets pane.")
        keep_alive()  # 啟動 Flask 保活伺服器（獨立執行緒）
        client.run(token)
    except discord.HTTPException as e:
        if e.status == 429:
            print("Too many requests — Discord rate limit")
        else:
            raise e

