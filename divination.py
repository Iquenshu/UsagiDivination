import random
import discord
import os

# 占卜副程式
async def fortune_telling(message):
    results = ["Greatblessing", "Lucky", "Fine", "Bad", "Worse"]
    weights = [5, 20, 50, 20, 5]
    result = random.choices(results, weights=weights, k=1)[0]

    # 占卜結果文字
    result_text = {
        "Greatblessing": "🌞 超吉幸運！ 大吉",
        "Lucky": "🍀 好吉了! 吉",
        "Fine": "🙂 吉度安穩~ 末吉",
        "Bad": "🌧 壞吉了! 凶",
        "Worse": "緊吉情況! 大凶"
    }

    # 嘗試附上對應圖片（例如放在 Divination_images/Greatblessing.png）
    image_path = os.path.join("Divination_images", f"{result}.png")

    if os.path.exists(image_path):
        await message.channel.send(
            content=f"🎴 你的占卜結果是：**{result_text[result]}**",
            file=discord.File(image_path)
        )
    else:
        await message.channel.send(f"🎴 你的占卜結果是：**{result_text[result]}**")
