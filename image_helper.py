import os
import random

def get_random_image(result):
    """
    根據占卜結果名稱，從 Divinatin_images 對應資料夾隨機選圖
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(BASE_DIR, "Divinatin_images", result)

    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return None

    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    if not files:
        return None

    selected_file = random.choice(files)
    return os.path.join(folder_path, selected_file)
