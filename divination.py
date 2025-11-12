import random
import discord
import os
import time

# ===============================
# 全域防重觸發設定
# ===============================
user_last_time = {}      # 記錄每個使用者上次占卜時間
GLOBAL_COOLDOWN = 1.0    # 秒數：同一使用者 1 秒內不可重複觸發

# ===============================
# 占卜副程式
# ===============================
async def fortune_telling(message):
    """
    根據使用者訊息執行占卜，回覆文字 + 對應隨機圖檔
    """

    # -------------------------------
    # 防重觸發檢查
    # -------------------------------
    user_id = message.author.id
    now = time.time()
    if user_id in user_last_time and now - user_last_time[user_id] < GLOBAL_COOLDOWN:
        return
    user_last_time[user_id] = now

    # -------------------------------
    # 占卜結果機率設定
    # -------------------------------
    results = ["Greatblessing", "Lucky", "Fine", "Bad", "Worse"]
    weights = [5, 20, 50, 20, 5]  # 對應機率
    result = random.choices(results, weights=weights, k=1)[0]

    # -------------------------------
    # 占卜結果文字
    # -------------------------------
    result_text = {
        "Greatblessing": "🌞 超吉幸運！ 大吉",
        "Lucky": "🍀 好吉了! 吉",
        "Fine": "🙂 吉度安穩~ 末吉",
        "Bad": "🌧 壞吉了! 凶",
        "Worse": "💀 緊吉情況! 大凶"
    }

    # -------------------------------
    # 從對應資料夾隨機選圖
    # -------------------------------
    folder_path = os.path.join("Divination_images", result)
    image_file = None
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        if files:
            selected_file = random.choice(files)
            image_file = os.path.join(folder_path, selected_file)

    # -------------------------------
    # 一次回覆文字 + 圖片
    # -------------------------------
    if image_file:
        # 回覆文字 + 圖片
        await message.channel.send(
            content=f"🎴 你的占卜結果是：**{result_text[result]}**",
            file=discord.File(image_file)
        )
    else:
        # 若資料夾不存在或沒有圖檔，只回覆文字
        await message.channel.send(f"🎴 你的占卜結果是：**{result_text[result]}**")
