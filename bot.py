import urllib.request
import json
import os
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_GROUP_ID = os.environ.get("LINE_GROUP_ID")

def fetch_rss_titles(query, limit=3):
    """動態抓取當下最新鮮的 RSS 標題"""
    encoded_q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    titles = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=6) as response:
            root = ET.fromstring(response.read())
            for item in root.findall(".//item")[:limit]:
                t = item.find("title").text if item.find("title") is not None else ""
                if t:
                    titles.append(f"• {t}")
    except Exception as e:
        print(f"抓取關鍵字 ({query}) 發生錯誤: {e}")
        
    return titles

def generate_live_report():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d (%A)")
    current_hour = now.hour
    session_name = "早盤重點快報" if current_hour < 12 else "晚盤趨勢總結"

    # 1. 動態抓取美股台股最新標題
    stock_items = fetch_rss_titles("美股 台股 總經", 2)
    stock_content = "\n".join(stock_items) if stock_items else f"• 【即時監控 {now.strftime('%H:%M')}】全球股市與總經數據連線中。"

    # 2. 動態抓取房市房貸最新標題
    re_items = fetch_rss_titles("房貸 央行 房市 信用管制", 2)
    re_content = "\n".join(re_items) if re_items else f"• 【即時監控 {now.strftime('%H:%M')}】房市與央行政策動態連線中。"

    report = f"""
📈 【每日財經與房市{session_name}】 - {today_str}

📊 【總經與台美股市即時動態】
{stock_content}

🏠 【房市政策與實質動態追蹤】
{re_content}

💡 【系統時間戳記】
• 雲端生成時間：{now.strftime('%Y-%m-%d %H:%M:%S')} (即時抓取，絕無重複)

---
*🚀 雲端自動化即時情報推送*
""".strip()
    return report

def send_to_discord(content):
    if not DISCORD_WEBHOOK_URL or not content: return
    data = json.dumps({"content": content}).encode("utf-8")
    req = urllib.request.Request(
        DISCORD_WEBHOOK_URL, 
        data=data, 
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req) as res: 
            print("Discord 發送成功！狀態碼：", res.status)
    except Exception as e: 
        print("Discord 發送失敗：", e)

def send_to_line(content):
    if not LINE_TOKEN or not LINE_GROUP_ID or not content: return
    url = "https://api.line.me/v2/bot/message/push"
    payload_data = json.dumps({
        "to": LINE_GROUP_ID,
        "messages": [{"type": "text", "text": content}]
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload_data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    )
    try:
        with urllib.request.urlopen(req) as res: 
            print("LINE 發送成功！狀態碼：", res.status)
    except Exception as e: 
        print("LINE 發送失敗：", e)

if __name__ == "__main__":
    report_text = generate_live_report()
    if report_text:
        send_to_discord(report_text)
        send_to_line(report_text)
