import discord
import yt_dlp
import asyncio

# -------------------------------
# 音樂播放設定
# -------------------------------
# yt-dlp 設定 (負責取得音源)
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

# FFmpeg 設定 (負責轉檔給 Discord 聽)
ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

# -------------------------------
# 音樂佇列 (Queue) 系統
# -------------------------------
# 格式: {server_id: [song_info_dict, ...]}
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
        # 取得影片資訊 (不下載，只串流)
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # 如果是播放清單，只取第一個
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# -------------------------------
# 播放下一首的邏輯
# -------------------------------
def play_next(ctx, bot):
    guild_id = ctx.guild.id
    if guild_id in queues and len(queues[guild_id]) > 0:
        # 取出佇列中的下一首歌
        url = queues[guild_id].pop(0)
        
        # 由於 play_next 是由 callback 呼叫的 (非 async)，我們需要用 run_coroutine_threadsafe
        future = asyncio.run_coroutine_threadsafe(
            YTDLSource.from_url(url, loop=bot.loop, stream=True), bot.loop
        )
        try:
            player = future.result()
            # 遞迴：這首歌播完後，再呼叫 play_next
            ctx.voice_client.play(player, after=lambda e: play_next(ctx, bot))
            asyncio.run_coroutine_threadsafe(ctx.send(f"🎵 現在播放： **{player.title}**"), bot.loop)
        except Exception as e:
            print(f"播放錯誤: {e}")
            asyncio.run_coroutine_threadsafe(ctx.send(f"播放發生錯誤"), bot.loop)
    else:
        # 佇列空了
        asyncio.run_coroutine_threadsafe(ctx.send("✅ 播放清單已空，音樂結束！"), bot.loop)

# -------------------------------
# 指令功能函式
# -------------------------------

async def join(ctx):
    """加入使用者所在的語音頻道"""
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
    """離開語音頻道"""
    if ctx.voice_client:
        # 清空該群組的佇列
        if ctx.guild.id in queues:
            queues[ctx.guild.id].clear()
        await ctx.voice_client.disconnect()
        await ctx.send("👋 兔子跳走了 (已斷開連接)")
    else:
        await ctx.send("❌ 我不在任何語音頻道中")

async def play(ctx, url, bot):
    """播放音樂或加入佇列"""
    # 確保機器人在語音頻道
    if not ctx.voice_client:
        success = await join(ctx)
        if not success:
            return

    # 初始化該群組的佇列
    if ctx.guild.id not in queues:
        queues[ctx.guild.id] = []

    # 如果正在播放，加入佇列
    if ctx.voice_client.is_playing():
        queues[ctx.guild.id].append(url)
        await ctx.send(f"📝 已加入播放清單 (位置: {len(queues[ctx.guild.id])})")
    else:
        # 如果沒在播放，直接開始
        async with ctx.typing():
            try:
                player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
                ctx.voice_client.play(player, after=lambda e: play_next(ctx, bot))
                await ctx.send(f"🎵 現在播放： **{player.title}**")
            except Exception as e:
                await ctx.send(f"❌ 發生錯誤：{e}")

async def skip(ctx):
    """跳過目前歌曲"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop() # stop 會自動觸發 after 函式 (即 play_next)
        await ctx.send("⏭️ 已跳過歌曲")
    else:
        await ctx.send("❌ 目前沒有在播放音樂")

async def queue_list(ctx):
    """顯示播放清單"""
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        msg = "📜 **待播清單：**\n"
        for i, url in enumerate(queues[ctx.guild.id]):
            msg += f"{i+1}. {url}\n" # 這裡為了簡化顯示網址，進階版可以存標題
        await ctx.send(msg)
    else:
        await ctx.send("📭 目前播放清單是空的")
