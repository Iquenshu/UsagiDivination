import discord
import yt_dlp
import asyncio
import os

# 設定 FFmpeg 的路徑
FFMPEG_PATH = './ffmpeg' if os.path.exists('./ffmpeg') else 'ffmpeg'

# ---------------------------------------
# yt-dlp 設定 (偽裝成 Android 手機)
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
    
    # ✅ 嘗試讀取 cookies (如果有的話)
    'cookiefile': 'cookies.txt', 
    
    # ✅✅✅ 關鍵修改：強制偽裝成 Android 客戶端，繞過機器人偵測
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'ios']
        }
    },
    'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36',
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

queues = {}

# --- 除錯用：檢查 Cookies 檔案是否存在 ---
def debug_cookies():
    if os.path.exists('cookies.txt'):
        print("[System] ✅ 發現 cookies.txt 檔案！")
        # 讀取前幾行確認格式 (不顯示敏感內容)
        try:
            with open('cookies.txt', 'r') as f:
                content = f.read(100)
                if "youtube.com" in content or "google.com" in content:
                    print("[System] 檔案內容看起來是正確的 Netscape 格式。")
                else:
                    print("[System] ⚠️ 警告：cookies.txt 內容可能不是 Netscape 格式 (請確認是用擴充功能 Export 的)。")
        except:
            pass
    else:
        print("[System] ❌ 未發現 cookies.txt，將嘗試使用無登入模式 (Android 偽裝)。")

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        
        # 執行除錯檢查
        debug_cookies()

        try:
            # 嘗試下載資訊
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        except Exception as e:
            print(f"❌ 下載失敗: {e}")
            raise e

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, executable=FFMPEG_PATH, **ffmpeg_options), data=data)

# ------------------------------------------------
# 播放邏輯 (與之前相同)
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
    """加入使用者所在的語音頻道 (增強連線版)"""
    if not ctx.author.voice:
        await ctx.send("❌ 你必須先加入一個語音頻道！")
        return False
    
    channel = ctx.author.voice.channel

    # 檢查機器人是否已經在頻道中
    if ctx.voice_client is not None:
        # 如果已經在同一個頻道，直接回傳 True
        if ctx.voice_client.channel.id == channel.id:
            return True
        # 如果在不同頻道，嘗試移動
        try:
            await ctx.voice_client.move_to(channel)
            return True
        except Exception as e:
            await ctx.send(f"❌ 移動頻道失敗: {e}")
            return False
    else:
        # 嘗試連線 (關鍵修改處)
        try:
            # timeout=60: 延長等待時間到 60 秒
            # reconnect=True: 允許自動重連
            # self_deaf=True: 機器人進場自動拒聽 (節省頻寬，提高連線成功率)
            await channel.connect(timeout=60, reconnect=True, self_deaf=True)
            return True
        except asyncio.TimeoutError:
            await ctx.send("❌ 連線逾時 (Timeout)。\n請嘗試再次輸入指令，或檢查 Discord 群組的語音伺服器區域。")
            return False
        except Exception as e:
            await ctx.send(f"❌ 連線發生未知錯誤: {e}")
            print(f"[Join Error] {e}")
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
                player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
                ctx.voice_client.play(player, after=lambda e: play_next(ctx, bot))
                await ctx.send(f"🎵 現在播放： **{player.title}**")
            except Exception as e:
                error_msg = str(e)
                if "Sign in" in error_msg:
                    await ctx.send("❌ YouTube 拒絕存取。嘗試過多請求，IP 暫時被封鎖。")
                elif "Video unavailable" in error_msg:
                    await ctx.send("❌ 影片無法播放 (可能版權限制或私人影片)。")
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
