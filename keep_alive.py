import threading, time, requests, os
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "<h1>🐰 Usagi Bot is awake and running!</h1>"

def run():
    app.run(host='0.0.0.0', port=8080)

def ping_self():
    while True:
        try:
            # Render 自動提供 RENDER_EXTERNAL_URL 環境變數
            url = os.environ.get("RENDER_EXTERNAL_URL", "https://usagidivination.onrender.com")
            requests.get(url)
            print(f"[keep_alive] Pinged {url}")
        except Exception as e:
            print(f"[keep_alive] Ping failed: {e}")
        time.sleep(240)  # 每4分鐘ping一次（Render 休眠門檻是15分鐘）

def keep_alive():
    t1 = threading.Thread(target=run)
    t2 = threading.Thread(target=ping_self)
    t1.daemon = True
    t2.daemon = True
    t1.start()
    t2.start()

