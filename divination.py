import discord
import random
import time
import datetime
import asyncio
from image_helper import get_random_image

# -------------------------------
# 設定
# -------------------------------
USER_COOLDOWN = 2.0   # 每個使用者短時間冷卻 (秒)
DAILY_LIMIT = 3       # 一般使用者每日最大占卜次數
ADMIN_ROLES = ["管理"]  # 管理身分群名稱

# -------------------------------
# 資料結構
# -------------------------------
# user_id: 上次占卜時間 (冷卻)
user_last_time = {}

# user_id: {"date": YYYY-MM-DD, "count": int}
user_daily_count = {}

# -------------------------------
# 占卜主程式
# -------------------------------
async def fortune_telling(message):
    global user_last_time, user_daily_count

    user_id = message.author.id
    now = time.time()
    today_str = datetime.date.today().isoformat()

    # -------------------------------
    # 檢查是否為管理身分
    # -------------------------------
    is_admin = any(role.name in ADMIN_ROLES for role in getattr(message.author, "roles", []))

    # -------------------------------
    # 使用者冷卻檢查
    # -------------------------------
    if not is_admin:
        if user_id in user_last_time and now - user_last_time[user_id] < USER_COOLDOWN:
            return
        user_last_time[user_id] = now

    # -------------------------------
    # 每日占卜次數檢查
    # -------------------------------
    if not is_admin:
        if user_id not in user_daily_count or user_daily_count[user_id]["date"] != today_str:
            user_daily_count[user_id] = {"date": today_str, "count": 0}

        if user_daily_count[user_id]["count"] >= DAILY_LIMIT:
            await message.channel.send(
                f"🎴 你今日占卜次數已滿 ({DAILY_LIMIT}/{DAILY_LIMIT})"
            )
            return

        # 增加占卜次數
        user_daily_count[user_id]["count"] += 1
        current_count = user_daily_count[user_id]["count"]
    else:
        current_count = "∞"  # 管理者不受限制

    # -------------------------------
    # 占卜結果機率設定
    # -------------------------------
    results = ["Greatblessing", "Lucky", "Fine", "Bad", "Worse"]
    weights = [5, 20, 50, 20, 5]
    result = random.choices(results, weights=weights, k=1)[0]

    # -------------------------------
    # 占卜文字結果
    # -------------------------------
    result_text = {
        "Greatblessing": "🌞 超吉幸運！ 大吉",
        "Lucky": "🍀 好吉了! 吉",
        "Fine": "🙂 吉度安穩~ 末吉",
        "Bad": "🌧 壞吉了! 凶",
        "Worse": "💀 緊吉情況! 大凶"
    }

    # -------------------------------
    # 取得隨機圖檔
    # -------------------------------
    image_file = get_random_image(result)

    # -------------------------------
    # 文字 + 圖片一次回覆
    # -------------------------------
    count_text = f"(已占卜{current_count}/{DAILY_LIMIT}次)" if not is_admin else "(管理者無限制)"

    if image_file:
        await message.channel.send(
            content=f"🎴 你的占卜結果是：**{result_text[result]}** {count_text}",
            file=discord.File(image_file)
        )
    else:
        await message.channel.send(
            f"🎴 你的占卜結果是：**{result_text[result]}** {count_text}"
        )

# -------------------------------
# 每日重置任務
# -------------------------------
async def reset_daily_count_task():
    """
    每日午夜自動重置使用者占卜次數
    """
    global user_daily_count
    while True:
        now = datetime.datetime.now()
        # 計算下一個午夜時間
        tomorrow = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        wait_seconds = (tomorrow - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        user_daily_count.clear()
        print("[Divination] 已重置每日占卜次數")
