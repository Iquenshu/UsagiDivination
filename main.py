import discord
from discord.ext import commands # 必須有這行
from keep_alive import keep_alive
from divination import fortune_telling, reset_daily_count_task
import music # 必須有這行，且 music.py 必須存在
# 設定 FFmpeg 的路徑
FFMPEG_PATH = './ffmpeg' if os.path.exists('./ffmpeg') else 'ffmpeg'

# ---------------------------------------
# 更新：加入 cookiefile 與 User Agent
# ---------------------------------------
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    # ✅ 關鍵修改 1: 讀取 Render Secret File 產生的 cookies.txt
    'cookiefile': 'cookies.txt', 
    # ✅ 關鍵修改 2: 偽裝成瀏覽器
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
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
        
        # 這裡會嘗試讀取 cookies，如果檔案不存在可能會報錯，但我們會依賴 Render 已建立檔案
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        except Exception as e:
            print(f"下載資訊錯誤 (可能是 Cookies 問題): {e}")
            raise e

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, executable=FFMPEG_PATH, **ffmpeg_options), data=data)

# ... (以下的 play_next, join, leave, play 等函式保持原本的樣子即可，不需要更動) ...

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
    if not ctx.author.voice:
        await ctx.send("❌ 你必須先加入一個語音頻道！")
        return False
    channel = ctx.author.voice.channel
    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()
    return True

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
                # 這裡會使用新的設定 (含 cookies)
                player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
                ctx.voice_client.play(player, after=lambda e: play_next(ctx, bot))
                await ctx.send(f"🎵 現在播放： **{player.title}**")
            except Exception as e:
                # 捕捉錯誤並顯示給你看，方便除錯
                error_msg = str(e)
                if "Sign in" in error_msg:
                    await ctx.send(f"❌ YouTube 拒絕存取 (Cookies 可能過期或無效)")
                else:
                    await ctx.send(f"❌ 發生錯誤：{error_msg}")

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


