import discord
import random
import time
from image_helper import get_random_image

# -------------------------------
# 防重觸發設定
# -------------------------------
user_last_time = {}
GLOBAL_COOLDOWN = 1.0  # 秒

# -------------------------------
# 占卜主程式
# -------------------------------
async def fortune_telling(message):
    user_id = message.author.id
    now = time.time()

    # 檢查使用者冷卻
    if user_id in user_last_time and now - user_last_time[user_id] < GLOBAL_COOLDOWN:
        return
    user_last_time[user_id] = now

    # 占卜結果機率設定
    results = ["Greatblessing", "Lucky", "Fine", "Bad", "Worse"]
    weights = [5, 20, 50, 20, 5]
    result = random.choices(results, weights=weights, k=1)[0]

    # 占卜文字結果
    result_text = {
        "Greatblessing": "🌞 超吉幸運！ 大吉",
        "Lucky": "🍀 好吉了! 吉",
        "Fine": "🙂 吉度安穩~ 末吉",
        "Bad": "🌧 壞吉了! 凶",
        "Worse": "💀 緊吉情況! 大凶"
    }

    # 取得隨機圖檔
    image_file = get_random_image(result)

    # 文字 + 圖片一次回覆
    if image_file:
        await message.channel.send(
            content=f"🎴 你的占卜結果是：**{result_text[result]}**",
            file=discord.File(image_file)
        )
    else:
        await message.channel.send(f"🎴 你的占卜結果是：**{result_text[result]}**")

