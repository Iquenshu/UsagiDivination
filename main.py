import os
import discord
import asyncio
from discord.ext import commands  # 引入 commands 擴充
from keep_alive import keep_alive
from divination import fortune_telling, reset_daily_count_task
import music  # 引入剛剛建立的 music.py

# 設定 Intent
intents = discord.Intents.default()
intents.message_content = True

# 將 Client 改為 Bot，並設定指令前綴 (例如 $)
bot = commands.Bot(command_prefix='$', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    # 啟動每日重置任務
    bot.loop.create_task(reset_daily_count_task())

# ------------------------------------------------
# 既有的占卜功能 (保留 on_message)
# ------------------------------------------------
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # 保留原本的文字觸發邏輯
    if message.content == "吉占卜":
        await fortune_telling(message)
    
    # 必須加上這一行，不然 commands 指令會被 on_message 蓋掉
    await bot.process_commands(message)

# ------------------------------------------------
# 新增的音樂指令
# ------------------------------------------------
@bot.command()
async def hello(ctx):
    await ctx.send('Hello!')

@bot.command()
async def join(ctx):
    """指令: $join - 讓兔子進來語音頻道"""
    await music.join(ctx)

@bot.command()
async def leave(ctx):
    """指令: $leave - 讓兔子離開"""
    await music.leave(ctx)

@bot.command()
async def play(ctx, url: str):
    """指令: $play <網址> - 播放 YouTube 音樂"""
    await music.play(ctx, url, bot)

@bot.command()
async def skip(ctx):
    """指令: $skip - 跳過這首歌"""
    await music.skip(ctx)

@bot.command()
async def list(ctx):
    """指令: $list - 查看播放清單"""
    await music.queue_list(ctx)

# ------------------------------------------------
# 啟動
# ------------------------------------------------
if __name__ == "__main__":
    try:
        token = os.getenv("TOKEN") or ""
        if token == "":
            raise Exception("Please add your token to the Secrets pane.")
        keep_alive()
        bot.run(token)
    except discord.HTTPException as e:
        if e.status == 429:
            print("Too many requests — Discord rate limit")
        else:
            raise e


