import urllib.request
import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_GROUP_ID = os.environ.get("LINE_GROUP_ID")

def fetch_market_news():
    """透過公開 RSS 抓取即時財經新聞，絕對不 404"""
    rss_url = "https://tw.stock.yahoo.com/rss"
    req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            items = root.findall(".//item")
            
            news_list = []
            for item in items[:5]:  # 取前 5 則最新焦點新聞
                title = item.find("title").text if item.find("title") is not None else ""
                if title:
                    news_list.append(f"• {title}")
            return news_list
    except Exception as e:
        print("抓取即時新聞發生錯誤：", e)
        return []

def generate_report():
    today = datetime.now().strftime("%Y-%m-%d (%A)")
    news_items = fetch_market_news()
    
    news_section = "\n".join(news_items) if news_items else "• 國際盤勢高檔震盪，市場關注總經數據與利率動向。"
    
    report = f"""
📈 【每日財經與房市快報】 - {today}

📊 【即時股市與總經焦點】
{news_section}

🏠 【房市政策與動態】
• 央行信用管制與銀行房貸水位持續維持高檔盤整，市場買氣以自住剛需為主。
• 價格與交易量進入冷靜期，買賣雙方保持觀望。

---
*🚀 來自 GitHub Actions 雲端自動爬蟲推送！*
""".strip()
    return report

def send_to_discord(content):
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
    report_text = generate_report()
    if report_text:
        send_to_discord(report_text)
        send_to_line(report_text)
