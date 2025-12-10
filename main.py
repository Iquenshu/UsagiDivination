import os
import discord
import asyncio
from discord.ext import commands
from keep_alive import keep_alive
# 引用原本的占卜功能
from divination import fortune_telling, reset_daily_count_task

# ❌ 移除這行: import music

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

    # 這行保留，確保指令擴充性
    await bot.process_commands(message)

# ❌ 移除所有 @bot.command() async def play/join/leave ... 等音樂指令

if __name__ == "__main__":
    try:
        token = os.getenv("TOKEN")
        if not token:
            print("錯誤：找不到 TOKEN，請檢查 Render 環境變數。")
        else:
            keep_alive()
            bot.run(token)
    except discord.HTTPException as e:
        if e.status == 429:
            print("🚨 嚴重錯誤：Discord Rate Limit (請求次數過多)")
            print("請停止部署，等待 1 小時後再試。")
            import time
            time.sleep(3600) 
        else:
            raise e
