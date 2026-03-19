import os
import sys
import subprocess
import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

# 新增資料庫模組
import database

# 讀取 .env 檔案
load_dotenv()

from divination import fortune_telling, reset_daily_count_task

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='$', intents=intents)

# ==========================================
# 系統設定區
# ==========================================
OWNER_ID = 272394340624629760  # 你的專屬 Discord ID
PROJECT_PATH = r'C:\Users\Administrator\UsagiDivination'  # 鎖定專案路徑

def get_git_commit():
    """取得當前 Git 儲存庫的最新 Commit 版本號 (前 7 碼)"""
    try:
        commit = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'], 
            cwd=PROJECT_PATH
        ).decode('utf-8').strip()
        return commit
    except Exception as e:
        return f"未知 (獲取失敗: {e})"

# ==========================================
# 啟動事件：發送重啟完畢與版本資訊
# ==========================================
@bot.event
async def on_ready():
    # 開機時自動檢查並建立資料庫與表格
    database.init_db()
    
    print(f'We have logged in as {bot.user}')
    bot.loop.create_task(reset_daily_count_task())
    
    # 每次開機/重啟成功後，在測試頻道廣播最新狀態
    commit_hash = get_git_commit()
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.name == "測試":
                await channel.send(
                    f"✅ **[系統通知]** 機器人服務已啟動並連線！\n"
                    f"🏷️ **當前程式碼版本 (Commit):** `{commit_hash}`"
                )
                break  # 找到頻道發送後就跳出迴圈

# ==========================================
# 訊息處理事件
# ==========================================
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # ------------------------------------------
    # 👑 專屬管理指令：遠端更新與重啟
    # ------------------------------------------
    if message.content == "$更新":
        # 限制 1：只能在「測試」頻道使用
        if message.channel.name != "測試":
            return
            
        # 限制 2：驗證是不是主人的 Discord ID
        if message.author.id != OWNER_ID:
            await message.channel.send("❌ **[拒絕存取]** 權限不足：您不是系統管理員！")
            return

        await message.channel.send("⏳ **[系統通知]** 權限驗證通過！正在從 GitHub 拉取最新程式碼...")
        
        try:
            # 讓機器人自己在背景執行 git pull
            output = subprocess.check_output(
                ['git', 'pull', 'origin', 'windows-server'], 
                stderr=subprocess.STDOUT,
                cwd=PROJECT_PATH
            ).decode('utf-8')
            
            await message.channel.send(
                f"📥 **[Git 拉取成功]** 檔案更新結果：\n```text\n{output}```\n"
                f"🔄 **[系統通知]** 準備強制終止處理程序，等待系統重啟..."
            )
        except subprocess.CalledProcessError as e:
            # 如果發生衝突或錯誤，回傳日誌
            error_output = e.output.decode('utf-8')
            await message.channel.send(f"❌ **[錯誤]** 拉取失敗，請確認 GitHub 狀態。\n```text\n{error_output}```")
            return

        # 強制結束程式。這會觸發 NSSM 立刻用 Administrator 權限把它重新開機！
        os._exit(0)

    # ------------------------------------------
    # 👥 一般使用者功能區 (頻道限制)
    # ------------------------------------------
    allowed_channels = ["一般", "測試"]
    if message.channel.name not in allowed_channels:
        return

    # 占卜觸發
    if message.content == "吉占卜":
        await fortune_telling(message)

    # 📊 新增：個人統計查詢指令
    elif message.content == "$統計":
        stats = database.get_user_stats(message.author.id)
        if not stats:
            await message.channel.send(f"{message.author.mention} 你還沒有抽過吉占卜喔！趕快來試試手氣吧！")
            return
            
        # 計算機率並排版輸出
        t = stats['total']
        msg = (
            f"📊 **{stats['name']} 的吉占卜生涯統計** 📊\n"
            f"總共占卜了 **{t}** 次\n"
            f"✨ 大吉: {stats['great']} 次 ({stats['great']/t*100:.1f}%)\n"
            f"🍀 吉: {stats['lucky']} 次 ({stats['lucky']/t*100:.1f}%)\n"
            f"👌 末吉: {stats['fine']} 次 ({stats['fine']/t*100:.1f}%)\n"
            f"🌧️ 凶: {stats['bad']} 次 ({stats['bad']/t*100:.1f}%)\n"
            f"💀 大凶: {stats['worse']} 次 ({stats['worse']/t*100:.1f}%)"
        )
        await message.channel.send(msg)

    # 🏆 新增：排行榜查詢指令
    elif message.content == "$排行":
        top_users = database.get_top_users(5) # 取前 5 名
        if not top_users:
            await message.channel.send("目前還沒有任何人留下占卜紀錄！")
            return
            
        msg = "🏆 **吉占卜狂熱者排行榜 TOP 5** 🏆\n"
        for i, user in enumerate(top_users):
            msg += f"第 {i+1} 名：**{user[0]}** (共抽了 {user[1]} 次)\n"
        await message.channel.send(msg)

    elif message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    await bot.process_commands(message)


if __name__ == "__main__":
    token = os.getenv("TOKEN")
    if not token:
        print("錯誤：找不到 TOKEN，請檢查 .env 檔案設定。")
    else:
        try:
            bot.run(token)
        except discord.HTTPException as e:
            if e.status == 429:
                print("🚨 嚴重錯誤：Discord Rate Limit (請求次數過多)")
            raise e