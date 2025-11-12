import discord
import random
import time
from image_helper import get_random_image

# -------------------------------
# 全域冷卻設定
# -------------------------------
GLOBAL_COOLDOWN = 1.0  # 秒，整個頻道占卜冷卻時間
last_fortune_time = 0   # 上次占卜時間

# -------------------------------
# 占卜主程式
# -------------------------------
async def fortune_telling(message):
    global last_fortune_time
    now = time.time()

    # -------------------------------
    # 全域冷卻檢查
    # -------------------------------
    if now - last_fortune_time < GLOBAL_COOLDOWN:
        # 如果還在冷卻時間內，不回覆
        return
    last_fortune_time = now

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
    if image_file:
        await message.channel.send(
            content=f"🎴 你的占卜結果是：**{result_text[result]}**",
            file=discord.File(image_file)
        )
    else:
        await message.channel.send(f"🎴 你的占卜結果是：**{result_text[result]}**")


