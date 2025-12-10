import os
import discord
import asyncio
from discord.ext import commands
from keep_alive import keep_alive
# 引用原本的占卜功能
from divination import fortune_telling, reset_daily_count_task

intents = discord.Intents.default()
intents.message_content = True

# 設定指令前綴為 $
bot = commands.Bot(command_prefix='$', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    # 啟動每日重置任務
    bot.loop.create_task(reset_daily_count_task())

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # 占卜觸發
    if message.content == "吉占卜":
        await fortune_telling(message)

    # 測試指令
    elif message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    await bot.process_commands(message)

if __name__ == "__main__":
    try:
        token = os.getenv("TOKEN")
        if not token:
            print("錯誤：找不到 TOKEN，請檢查 Render 環境變數。")
        else:
            keep_alive()  # 啟動網頁伺服器保持在線
            bot.run(token)
    except discord.HTTPException as e:
        if e.status == 429:
            print("🚨 嚴重錯誤：Discord Rate Limit (請求次數過多)")
            print("請停止部署，等待 1~2 小時後再試。")
            # 讓程式暫停，避免 Render 一直重啟導致封鎖時間加長
            import time
            time.sleep(3600) 
        else:
            raise e
