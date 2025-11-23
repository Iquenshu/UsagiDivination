import discord
import yt_dlp
import asyncio
import os

# 設定 FFmpeg 的路徑 (對應 build.sh 下載的位置)
FFMPEG_PATH = './ffmpeg' if os.path.exists('./ffmpeg') else 'ffmpeg'

# yt-dlp 設定
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
}

ffmpeg_options = {
    'options': '-vn',
    # 這行確保從上次中斷處重連，減少中斷
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

# 播放清單字典 {guild_id: [url1, url2, ...]}
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
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        # 關鍵：指定 executable 為我們下載的 ffmpeg
        return cls(discord.FFmpegPCMAudio(filename, executable=FFMPEG_PATH, **ffmpeg_options), data=data)

def play_next(ctx, bot):
    """遞迴函數：播完一首後自動播下一首"""
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
    else:
        asyncio.run_coroutine_threadsafe(ctx.send("✅ 播放清單已空，音樂結束！"), bot.loop)

# --- 指令功能 ---

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
                player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
                ctx.voice_client.play(player, after=lambda e: play_next(ctx, bot))
                await ctx.send(f"🎵 現在播放： **{player.title}**")
            except Exception as e:
                await ctx.send(f"❌ 錯誤：{e}")

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
