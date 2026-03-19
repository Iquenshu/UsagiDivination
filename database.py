import sqlite3
import datetime

DB_FILE = 'usagi_stats.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 原本的總計表
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
    # 🌟 新增：歷史紀錄表 (用來計算「本月」的數據)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS draw_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            user_name TEXT,
            category TEXT,
            draw_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

def record_draw(user_id, user_name, result_category):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. 更新總計表
    cursor.execute('INSERT OR IGNORE INTO user_stats (user_id, user_name) VALUES (?, ?)', (str(user_id), user_name))
    
    category_map = {"Greatblessing": "great_blessing", "Lucky": "lucky", "Fine": "fine", "Bad": "bad", "Worse": "worse"}
    db_column = category_map.get(result_category)
    if db_column:
        cursor.execute(f'''
            UPDATE user_stats 
            SET total_draws = total_draws + 1, {db_column} = {db_column} + 1, user_name = ? 
            WHERE user_id = ?
        ''', (user_name, str(user_id)))

    # 2. 新增一筆歷史紀錄 (存入當下的台灣時間，方便日後算「本月」)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO draw_history (user_id, user_name, category, draw_time)
        VALUES (?, ?, ?, ?)
    ''', (str(user_id), user_name, result_category, now_str))
        
    conn.commit()
    conn.close()

def get_user_stats(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_stats WHERE user_id = ?', (str(user_id),))
    row = cursor.fetchone()
    conn.close()
    
    if not row or row[2] == 0: return None
    return {"name": row[1], "total": row[2], "great": row[3], "lucky": row[4], "fine": row[5], "bad": row[6], "worse": row[7]}