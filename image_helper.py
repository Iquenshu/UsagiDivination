import os
import random

# 用來記憶每個運勢類別目前的「圖片卡池」
# 格式: { "Bad": ["img1.jpg", "img2.jpg"], "Lucky": [...] }
_image_pools = {}

def get_random_image(result):
    """
    根據占卜結果名稱，從 Divinatin_images 對應資料夾選圖。
    採用「洗牌袋」機制：保證該資料夾內所有圖片都出現過一次後，才會開始重複。
    """
    global _image_pools
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(BASE_DIR, "Divinatin_images", result)

    # 檢查資料夾是否存在
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return None

    # 如果這個運勢的卡池還沒建立，或是卡池已經空了 (圖都發完了)
    # 就重新讀取資料夾並洗牌
    if result not in _image_pools or not _image_pools[result]:
        # 讀取該資料夾下所有檔案
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        
        if not files:
            return None
            
        # 隨機洗牌
        random.shuffle(files)
        # 存入卡池
        _image_pools[result] = files
        print(f"[System] 已重置圖片卡池: {result} (共 {len(files)} 張)")

    # 從卡池中取出一張 (pop 會移除該項目)
    selected_file = _image_pools[result].pop()
    
    return os.path.join(folder_path, selected_file)
