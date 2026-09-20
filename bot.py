import urllib.request
import json
import os
from datetime import datetime

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_GROUP_ID = os.environ.get("LINE_GROUP_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def generate_live_market_report():
    today = datetime.now().strftime("%Y-%m-%d (%A)")
    
    if not GEMINI_API_KEY:
        return f"【財經快報】 - {today} 錯誤：未設定 GEMINI_API_KEY。"

    # 使用支援 Google Search 聯網功能的 Gemini API 點
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 精準 Prompt，要求 AI 自動搜尋最新股市與房市政策
    prompt = f"""
    請擔任專業金融與房市從業人員，幫我搜尋並整理一份今日（日期：{today}）的最新市場快報。
    請利用網路搜尋最新動態，並包含以下重點，語氣俐落專業、乾貨滿點：
    
    📈 【每日財經與房市快報】 - {today}
    
    📊 【股市與總經要聞】
    • 美國與國際盤勢：主要指數表現、近期重要總經數據（如 CPI、非農或聯準會動向）。
    • 亞股動態：台股、日股、韓股的近期指數相關資訊與盤面焦點。
    
    🏠 【房市政策與動態】
    • 貸款政策與利率：近期央行信用管制、銀行房貸水位或不動產融資的最新政策更新。
    • 市場實際狀況：重劃區或整體房市的交易與價格觀察。
    
    ---
    *🚀 來自 GitHub Actions 雲端 AI 機器人自動聯網推送！*
    """
    
    # 關鍵：開啟 Google Search Grounding 聯網工具，讓 AI 抓取最新即時資料
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"googleSearch": {}}]
    }).encode("utf-8")
    
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode("utf-8"))
            text_content = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            print("AI 即時聯網內容生成成功！")
            return text_content
    except Exception as e:
        print("AI 聯網生成失敗：", e)
        return f"【財經快報】 - {today} 系統暫時無法取得即時 AI 內容 (錯誤: {e})"

def send_to_discord(content):
    if not DISCORD_WEBHOOK_URL: return
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
    if not LINE_TOKEN or not LINE_GROUP_ID: return
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
        with urllib.request.urlopen(req) as res: 
            print("LINE 發送成功！狀態碼：", res.status)
    except Exception as e: 
        print("LINE 發送失敗：", e)

if __name__ == "__main__":
    report_text = generate_live_market_report()
    send_to_discord(report_text)
    send_to_line(report_text)
