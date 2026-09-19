import urllib.request
import json
import os
from datetime import datetime

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_GROUP_ID = os.environ.get("LINE_GROUP_ID")

def get_market_summary():
    today = datetime.now().strftime("%Y-%m-%d")
    message = f"""
📈 【每日財經與房市快報】 - {today}

📊 【股市與總經要聞】
• 美國與國際：市場聚焦最新通膨數據與聯準會利率走向，科技股震盪整理。
• 台股動態：權值股近期表現牽動大盤，法人資金持續輪動，留意成交量變化與匯率波動。
• 總經指標：出口數據與景氣對策燈號持續為市場風向球。

🏠 【房市最新動態】
• 政策與利率：央行信用管制與房貸水位相對緊縮，市場交易節奏放緩，以自住與換屋需求為主。
• 區域焦點：六都及主要重劃區預售屋實價登錄價格波動趨於平穩，建商推案策略轉趨保守觀望。

---
*🚀 來自 GitHub Actions 雲端機器人自動推送！*
"""
    return message.strip()

def send_to_discord(content):
    if not DISCORD_WEBHOOK_URL:
        print("未設定 Discord Webhook 網址")
        return
        
    data = json.dumps({"content": content}).encode("utf-8")
    req = urllib.request.Request(
        DISCORD_WEBHOOK_URL, 
        data=data, 
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            print("Discord 發送成功！狀態碼：", response.status)
    except Exception as e:
        print("Discord 發送失敗：", e)

def send_to_line(content):
    if not LINE_TOKEN or not LINE_GROUP_ID:
        print("未設定 LINE Token 或 Group ID，跳過 LINE 發送")
        return
        
    url = "https://api.line.me/v2/bot/message/push"
    data = json.dumps({
        "to": LINE_GROUP_ID,
        "messages": [{"type": "text", "text": content}]
    }).encode("utf-8")
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_TOKEN}"
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            print("LINE 發送成功！狀態碼：", response.status)
    except Exception as e:
        print("LINE 發送失敗：", e)

if __name__ == "__main__":
    content = get_market_summary()
    send_to_discord(content)
    send_to_line(content)
