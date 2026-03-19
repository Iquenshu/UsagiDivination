import sqlite3
import os

# 資料庫檔案名稱
DB_FILE = 'usagi_stats.db'

def init_db():
    """初始化資料庫與表格 (如果沒有的話會自動建立)"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 建立使用者統計表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id TEXT PRIMARY KEY,
            user_name TEXT,
            total_draws INTEGER DEFAULT 0,
            great_blessing INTEGER DEFAULT 0,
            lucky INTEGER DEFAULT 0,
            fine INTEGER DEFAULT 0,
            bad INTEGER DEFAULT 0,
            worse INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def record_draw(user_id, user_name, result_category):
    """記錄一次抽籤結果"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 先確保資料庫裡有這個人 (沒有就新增一筆歸零的資料)
    cursor.execute('''
        INSERT OR IGNORE INTO user_stats (user_id, user_name) 
        VALUES (?, ?)
    ''', (str(user_id), user_name))
    
    # 根據抽到的結果，更新對應的欄位與總次數
    # 假設你的分類對應是：Greatblessing, Lucky, Fine, Bad, Worse
    category_map = {
        "Greatblessing": "great_blessing",
        "Lucky": "lucky",
        "Fine": "fine",
        "Bad": "bad",
        "Worse": "worse"
    }
    
    db_column = category_map.get(result_category)
    if db_column:
        cursor.execute(f'''
            UPDATE user_stats 
            SET total_draws = total_draws + 1, 
                {db_column} = {db_column} + 1,
                user_name = ? 
            WHERE user_id = ?
        ''', (user_name, str(user_id)))
        
    conn.commit()
    conn.close()

def get_user_stats(user_id):
    """取得單一使用者的統計數據與比例"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_stats WHERE user_id = ?', (str(user_id),))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    # row 的內容對應: (user_id, user_name, total, great, lucky, fine, bad, worse)
    total = row[2]
    if total == 0:
        return None
        
    stats = {
        "name": row[1],
        "total": total,
        "great": row[3],
        "lucky": row[4],
        "fine": row[5],
        "bad": row[6],
        "worse": row[7]
    }
    return stats

def get_top_users(limit=5):
    """取得抽籤總次數排行榜"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT user_name, total_draws FROM user_stats ORDER BY total_draws DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows