import os
import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv  # 新增：用來讀取 .env 檔案

# 讀取 .env 檔案裡面的 TOKEN
load_dotenv()

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

    # >>> 新增這兩行：如果頻道名稱不是「測試」，就直接忽略這則訊息 <<<
    if message.channel.name != "測試":
        return

    # 占卜觸發
    if message.content == "吉占卜":
        await fortune_telling(message)

    # 測試指令
    elif message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    # 這行保留，確保指令擴充性
    await bot.process_commands(message)


if __name__ == "__main__":
    token = os.getenv("TOKEN")
    if not token:
        print("錯誤：找不到 TOKEN，請檢查 .env 檔案設定。")
    else:
        # 注意：這裡已經拿掉了 keep_alive()，因為 NSSM 會負責背景運行
        try:
            bot.run(token)
        except discord.HTTPException as e:
            if e.status == 429:
                print("🚨 嚴重錯誤：Discord Rate Limit (請求次數過多)")
                raise e 
            else:
                raise e