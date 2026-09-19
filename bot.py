import urllib.request
import json
import os
from datetime import datetime

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_GROUP_ID = os.environ.get("LINE_GROUP_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def generate_report():
    # 取得目前的 UTC 時間並轉成台灣時間的小時，用來判斷是早報還是晚報
    # GitHub Actions 預設是 UTC 時間
    current_hour_utc = datetime.utcnow().hour
    # 00:00 UTC = 08:00 台灣時間 (早報)
    # 09:00 UTC = 17:00 台灣時間 (晚報)
    is_morning = (current_hour_utc < 5) # 簡單用區段判斷，或由 workflow 帶參數
    
    today = datetime.now().strftime("%Y-%m-%d (%A)")
    
    if GEMINI_API_KEY:
        # 使用支援聯網與最新數據的 gemini 模型
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        # 根據早晚動態切換 Prompt
        if is_morning or current_hour_utc == 0:
            prompt = f"""
            請以專業金融從業人員的視角，為我撰寫一份今日的「早安財經與房市晨報」（日期：{today}）。
            請確保內容包含以下重點，語氣俐落專業：
            
            🌅 【早安財經與房市晨報】 - {today}
            
            📊 【股市與總經面】
            • 美股表現：列出主要指數（道瓊、標普、那斯達克、費半）的最新漲跌狀況。
            • 重要經濟數據提醒：特別檢視近期或當週是否有重大事件（如 CPI、非農就業數據等），若有請特別標註說明。
            • 亞股動態：提供台股、日股、韓股的最新指數相關資訊。
            
            🏠 【房市政策面】
            • 貸款政策更新：追蹤近期央行信用管制、銀行房貸水位或相關不動產融資政策的最新動態。
            
            ---
            *🚀 來自 GitHub Actions 雲端 AI 機器人自動推送！*
            """
        else:
            prompt = f"""
            請以專業金融從業人員的視角，為我撰寫一份今日的「台股收盤快報」（日期：{today}）。
            請確保內容包含以下重點，語氣俐落專業：
            
            🌇 【台股收盤快報】 - {today}
            
            📈 【台股收盤總結】
            • 加權指數收盤點位、漲跌幅與成交量。
            • 盤面焦點與主流類股表現（如權值股、強勢族群、法人動向）。
            
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
                return res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print("Gemini 生成失敗：", e)

    return f"【財經快報】 - {today} 系統暫時無法取得 AI 內容。"

def send_to_discord(content):
    if not DISCORD_WEBHOOK_URL: return
    data = json.dumps({"content": content}).encode("utf-8")
    req = urllib.request.Request(DISCORD_WEBHOOK_URL, data=data, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as res: print("Discord 發送成功：", res.status)
    except Exception as e: print("Discord 失敗：", e)

def send_to_line(content):
    if not LINE_TOKEN or not LINE_GROUP_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    data = json.dumps({"to": LINE_GROUP_ID, "messages": [{"type": "text", "text": content}]}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"})
    try:
        with urllib.request.urlopen(req) as res: print("LINE 發送成功：", res.status)
    except Exception as e: print("LINE 失敗：", e)

if __name__ == "__main__":
    content = generate_report()
    send_to_discord(content)
    send_to_line(content)
