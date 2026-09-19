import urllib.request
import json
import os
from datetime import datetime

# 從 GitHub 秘密保險箱安全讀取網址
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def get_market_summary():
    today = datetime.now().strftime("%Y-%m-%d")
    message = f"""
📈 **【每日財經與房市快報】** - {today}

📊 **【股市與總經要聞】**
• **美股與國際**：市場聚焦最新通膨數據與聯準會利率走向，科技股震盪整理。
• **台股動態**：權值股近期表現牽動大盤，法人資金持續輪動，留意成交量變化與匯率波動。
• **總經指標**：出口數據與景氣對策燈號持續為市場風向球。

🏠 **【房市最新動態】**
• **政策與利率**：央行信用管制與房貸水位相對緊縮，市場交易節奏放緩，以自住與換屋需求為主。
• **區域焦點**：六都及主要重劃區預售屋實價登錄價格波動趨於平穩，建商推案策略轉趨保守觀望。

---
*🚀 來自 GitHub Actions 雲端機器人自動推送！*
"""
    return message.strip()

def send_to_discord():
    if not WEBHOOK_URL:
        print("錯誤：找不到 DISCORD_WEBHOOK_URL 密鑰！")
        return
        
    content = get_market_summary()
    data = json.dumps({"content": content}).encode("utf-8")
    req = urllib.request.Request(WEBHOOK_URL, data=data, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req) as response:
            print("發送成功！狀態碼：", response.status)
    except Exception as e:
        print("發送失敗：", e)

if __name__ == "__main__":
    send_to_discord()
