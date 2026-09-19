import urllib.request
import json
import os
from datetime import datetime

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_GROUP_ID = os.environ.get("LINE_GROUP_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def generate_ai_market_summary():
    today = datetime.now().strftime("%Y-%m-%d (%A)")
    
    # 如果有設定 Gemini API，就讓 AI 即時生成專業快報
    if GEMINI_API_KEY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        prompt = f"""
        請以專業金融與房市從業人員的視角，為我撰寫一份「每日財經與房市快報」（日期：{today}）。
        排版格式需包含以下區塊，語氣專業、俐落、切中要害：
        
        📈 【每日財經與房市快報】 - {today}
        
        📊 【股市與總經要聞】
        • 美國與國際：...
        • 台股動態：...
        • 總經指標：...
        
        🏠 【房市最新動態】
        • 政策與利率：...
        • 區域焦點：...
        
        ---
        *🚀 來自 GitHub Actions 雲端 AI 機器人自動推送！*
        """
        
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}]
        }).encode("utf-8")
        
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                ai_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                return ai_text.strip()
        except Exception as e:
            print(generate_ai_market_summary, "Gemini 生成失敗，改用預設備用文字：", e)

    # 備用保底文字
    return f"""
📈 【每日財經與房市快報】 - {today}

📊 【股市與總經要聞】
• 國際與台股維持正常盤整，資金持續在各類股間輪動。

🏠 【房市最新動態】
• 房市受信用管制與房貸水位影響，市場以自住與換屋需求為主。

---
*🚀 來自 GitHub Actions 雲端機器人自動推送！*
""".strip()

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
    content = generate_ai_market_summary()
    send_to_discord(content)
    send_to_line(content)
