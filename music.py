import discord
import yt_dlp
import asyncio
import os

# 設定 FFmpeg 的路徑
# FFMPEG_PATH = './ffmpeg' if os.path.exists('./ffmpeg') else 'ffmpeg'
import shutil

# 讓系統自己去找 ffmpeg 在哪裡
FFMPEG_PATH = shutil.which("ffmpeg") or "ffmpeg"

print(f"使用的 FFmpeg 路徑: {FFMPEG_PATH}")



# 🔥🔥🔥 修改這裡開始：設定 Cookie 路徑 -----------------------
# 預設先找本地的 cookies.txt
cookie_path = 'cookies.txt'
# 如果發現 Render 的 Secret File 路徑有檔案，就改用那個路徑
if os.path.exists('/etc/secrets/cookies.txt'):
    cookie_path = '/etc/secrets/cookies.txt'

print(f"正在使用的 Cookie 路徑: {cookie_path}")
# -----------------------------------------------------------

# ---------------------------------------
# yt-dlp 設定
# ---------------------------------------
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': True,
    'quiet': False,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    
    # 🔥🔥🔥 修改這裡：移除舊的 oauth2，加入 cookiefile
    'cookiefile': cookie_path, 
    # 原本的 'username': 'oauth2' 和 'password': '' 都要刪掉
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

queues = {}

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        
        try:
            # 嘗試下載資訊
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        except Exception as e:
            print(f"❌ 下載失敗: {e}")
            # 這裡把錯誤丟出去，讓外層 play 函數捕獲
            raise e

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, executable=FFMPEG_PATH, **ffmpeg_options), data=data)

# ------------------------------------------------
# 播放邏輯
# ------------------------------------------------

def play_next(ctx, bot):
    if ctx.guild.id in queues and len(queues[ctx.guild.id]) > 0:
        url = queues[ctx.guild.id].pop(0)
        future = asyncio.run_coroutine_threadsafe(
            YTDLSource.from_url(url, loop=bot.loop, stream=True), bot.loop
        )
        try:
            player = future.result()
            ctx.voice_client.play(player, after=lambda e: play_next(ctx, bot))
            asyncio.run_coroutine_threadsafe(ctx.send(f"🎵 現在播放： **{player.title}**"), bot.loop)
        except Exception as e:
            print(f"播放錯誤: {e}")
            asyncio.run_coroutine_threadsafe(ctx.send(f"播放發生錯誤: {e}"), bot.loop)
    else:
        asyncio.run_coroutine_threadsafe(ctx.send("✅ 播放清單已空，音樂結束！"), bot.loop)

async def join(ctx):
    """加入語音頻道 (防呆版)"""
    if not ctx.author.voice:
        await ctx.send("❌ 你必須先加入一個語音頻道！")
        return False
    
    channel = ctx.author.voice.channel

    if ctx.voice_client is not None:
        if ctx.voice_client.channel.id == channel.id:
            return True
        try:
            await ctx.voice_client.move_to(channel)
            return True
        except:
            return False
    else:
        try:
            # 設定較長的 timeout 避免 Render 連線慢
            await channel.connect(timeout=60, reconnect=True, self_deaf=True)
            return True
        except asyncio.TimeoutError:
            await ctx.send("❌ 連線逾時，請再試一次。")
            return False
        except Exception as e:
            await ctx.send(f"❌ 連線錯誤: {e}")
            return False

async def leave(ctx):
    if ctx.voice_client:
        if ctx.guild.id in queues:
            queues[ctx.guild.id].clear()
        await ctx.voice_client.disconnect()
        await ctx.send("👋 兔子跳走了")
    else:
        await ctx.send("❌ 我不在語音頻道中")

async def play(ctx, url, bot):
    if not ctx.voice_client:
        if not await join(ctx):
            return

    if ctx.guild.id not in queues:
        queues[ctx.guild.id] = []

    if ctx.voice_client.is_playing():
        queues[ctx.guild.id].append(url)
        await ctx.send(f"📝 已加入清單 (第 {len(queues[ctx.guild.id])} 順位)")
    else:
        async with ctx.typing():
            try:
                # 這裡會觸發下載
                player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
                ctx.voice_client.play(player, after=lambda e: play_next(ctx, bot))
                await ctx.send(f"🎵 現在播放： **{player.title}**")
            except Exception as e:
                error_msg = str(e)
                # 移除了原本關於 OAuth2 登入的提示，因為現在是改用 Cookie
                await ctx.send(f"❌ 發生錯誤，可能因為版權或 Cookie 失效：{error_msg}")

async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ 跳過歌曲")

async def list_queue(ctx):
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        msg = "📜 **待播清單：**\n" + "\n".join([f"{i+1}. {url}" for i, url in enumerate(queues[ctx.guild.id])])
        await ctx.send(msg)
    else:
        await ctx.send("📭 清單是空的")
