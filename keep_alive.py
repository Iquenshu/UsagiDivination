from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>🐰 Usagi Bot is awake and running!</h1>'

def run():
    # Render 會自動抓 port=8080 作為 service port
    # 若改為其他 port 將導致健康檢查失敗
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """在獨立執行緒啟動 Flask 保活伺服器"""
    thread = Thread(target=run)
    thread.daemon = True  # 若主程式結束，不需等待此執行緒
    thread.start()
