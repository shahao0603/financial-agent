import os
from datetime import datetime
from google import genai

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_GROUP_ID = os.environ.get("LINE_GROUP_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def generate_live_market_report():
    today = datetime.now().strftime("%Y-%m-%d (%A)")
    
    if not GEMINI_API_KEY:
        print("錯誤：未設定 GEMINI_API_KEY")
        return None

    try:
        # 初始化官方 SDK
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = f"""
        請以專業金融與房市從業人員的視角，為我撰寫一份今日（日期：{today}）的專業市場快報。
        內容需包含：
        1. 股市與總經要聞（美股主要指數、國際盤勢、台股/亞股焦點）。
        2. 房市政策與動態（貸款政策、信用管制、房市實際交易觀察）。
        請確保排版俐落、乾貨滿點，不要使用罐頭文字，展現即時專業度。
        """
        
        # 呼叫最新穩定模型
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        print("AI 內容即時生成成功！")
        return response.text.strip()
        
    except Exception as e:
        print("AI 生成發生錯誤，詳細原因：", e)
        # 如果真的出錯，直接回傳錯誤訊息，讓你一眼看出問題
        return f"【系統提示】今日 ({today}) AI 內容生成失敗，錯誤原因：{e}"

def send_to_discord(content):
    import urllib.request
    import json
    if not DISCORD_WEBHOOK_URL or not content: return
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
        with urllib.request.urlopen(req) as res: 
            print("Discord 發送成功！狀態碼：", res.status)
    except Exception as e: 
        print("Discord 發送失敗：", e)

def send_to_line(content):
    import urllib.request
    import json
    if not LINE_TOKEN or not LINE_GROUP_ID or not content: return
    url = "https://api.line.me/v2/bot/message/push"
    
    payload_data = json.dumps({
        "to": LINE_GROUP_ID,
        "messages": [{"type": "text", "text": content}]
    }).encode("utf-8")
    
    req = urllib.request.Request(
        url,
        data=payload_data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_TOKEN}"
        }
    )
    try:
        with urllib.request.urlopen(req) as res: 
            print("LINE 發送成功！狀態碼：", res.status)
    except Exception as e: 
        print("LINE 發送失敗：", e)

if __name__ == "__main__":
    report_text = generate_live_market_report()
    if report_text:
        send_to_discord(report_text)
        send_to_line(report_text)
