import sqlite3
import datetime

DB_FILE = 'usagi_stats.db'

# ==========================================
# 🌟 幸運分數矩陣 (字典對應)
# ==========================================
SCORE_MAP = {
    "great": 3,   # 大吉
    "lucky": 1,   # 吉
    "fine": 0,    # 末吉/中吉
    "bad": -1,    # 凶
    "worse": -3   # 大凶
}

def get_lucky_leaderboard(limit=3):
    """計算所有人的幸運分數，並回傳最高分前幾名"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT user_name, great_blessing, lucky, fine, bad, worse FROM user_stats')
    rows = cursor.fetchall()
    conn.close()

    user_scores = []
    for row in rows:
        name, great, lucky, fine, bad, worse = row
        # 套用矩陣計算總分
        score = (great * SCORE_MAP["great"] +
                 lucky * SCORE_MAP["lucky"] +
                 fine * SCORE_MAP["fine"] +
                 bad * SCORE_MAP["bad"] +
                 worse * SCORE_MAP["worse"])
        user_scores.append({"name": name, "score": score})

    # 依照分數由高到低排序
    user_scores.sort(key=lambda x: x["score"], reverse=True)
    return user_scores[:limit]

def get_monthly_luckiest():
    """取得本月最幸運的玩家 (大吉 + 吉 次數最多)"""
    current_month = datetime.datetime.now().strftime("%Y-%m")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 使用 CASE WHEN 來分別計算大吉與吉的次數，並將兩者相加排序
    cursor.execute('''
        SELECT user_name,
               SUM(CASE WHEN category = 'Greatblessing' THEN 1 ELSE 0 END) as great_count,
               SUM(CASE WHEN category = 'Lucky' THEN 1 ELSE 0 END) as lucky_count,
               SUM(CASE WHEN category IN ('Greatblessing', 'Lucky') THEN 1 ELSE 0 END) as total_lucky
        FROM draw_history 
        WHERE draw_time LIKE ?
        GROUP BY user_id 
        HAVING total_lucky > 0
        ORDER BY total_lucky DESC 
        LIMIT 1
    ''', (f"{current_month}%",))
    
    row = cursor.fetchone()
    conn.close()
    return row  # 回傳格式: (名稱, 大吉次數, 吉次數, 總次數)

def get_monthly_unluckiest():
    """取得本月最倒楣的玩家 (大凶 + 凶 次數最多)"""
    current_month = datetime.datetime.now().strftime("%Y-%m")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 使用 CASE WHEN 來分別計算大凶與凶的次數，並將兩者相加排序
    cursor.execute('''
        SELECT user_name,
               SUM(CASE WHEN category = 'Worse' THEN 1 ELSE 0 END) as worse_count,
               SUM(CASE WHEN category = 'Bad' THEN 1 ELSE 0 END) as bad_count,
               SUM(CASE WHEN category IN ('Worse', 'Bad') THEN 1 ELSE 0 END) as total_unlucky
        FROM draw_history 
        WHERE draw_time LIKE ?
        GROUP BY user_id 
        HAVING total_unlucky > 0
        ORDER BY total_unlucky DESC 
        LIMIT 1
    ''', (f"{current_month}%",))
    
    row = cursor.fetchone()
    conn.close()
    return row  # 回傳格式: (名稱, 大凶次數, 凶次數, 總次數)