import os
import discord
import asyncio
from discord.ext import commands
from keep_alive import keep_alive
# 引用原本的占卜功能
from divination import fortune_telling, reset_daily_count_task
# 引用新的音樂功能
import music

intents = discord.Intents.default()
intents.message_content = True

# 設定指令前綴為 $
bot = commands.Bot(command_prefix='$', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    bot.loop.create_task(reset_daily_count_task())

# -----------------
# 音樂指令區
# -----------------
@bot.command()
async def join(ctx):
    """讓機器人加入語音頻道"""
    await music.join(ctx)

@bot.command()
async def leave(ctx):
    """讓機器人離開"""
    await music.leave(ctx)

@bot.command()
async def play(ctx, url: str):
    """播放音樂： $play <Youtube網址>"""
    await music.play(ctx, url, bot)

@bot.command()
async def skip(ctx):
    """跳過目前歌曲"""
    await music.skip(ctx)

@bot.command(name="list")
async def queue_list(ctx):
    """查看播放清單"""
    await music.list_queue(ctx)

# -----------------
# 保留原本的文字觸發與占卜
# -----------------
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # 舊的占卜觸發方式
    if message.content == "吉占卜":
        await fortune_telling(message)

    # 這一行非常重要！沒有這行，上面的 $play 指令會失效
    await bot.process_commands(message)

if __name__ == "__main__":
    try:
        token = os.getenv("TOKEN")
        if not token:
            raise Exception("Please add your token to the Secrets pane.")
        keep_alive()
        bot.run(token)
    except discord.HTTPException as e:
        if e.status == 429:
            print("Too many requests — Discord rate limit")
        else:
            raise e

