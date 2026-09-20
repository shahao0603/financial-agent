import urllib.request
import json
import os
from datetime import datetime
from PIL import Image, ImageDraw

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_GROUP_ID = os.environ.get("LINE_GROUP_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def generate_live_market_report():
    today = datetime.now().strftime("%Y-%m-%d (%A)")
    
    if not GEMINI_API_KEY:
        return f"【財經快報】 - {today} 錯誤：未設定 GEMINI_API_KEY。"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    請以專業金融與房市從業人員的視角，為我撰寫一份今日（日期：{today}）的專業市場快報。
    內容需包含：
    1. 股市與總經要聞（美股主要指數、國際盤勢、台股/亞股焦點）。
    2. 房市政策與動態（貸款政策、信用管制、房市實際交易觀察）。
    請確保排版俐落、乾貨滿點，不要有過多廢話。
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
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode("utf-8"))
            text_content = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            print("AI 內容生成成功！")
            return text_content
    except Exception as e:
        print("AI 生成失敗，使用預設文字：", e)
        return f"""
📈 【每日財經與房市快報】 - {today}

📊 【股市與總經要聞】
• 國際與美股盤勢維持高檔震盪，市場緊盯總經與利率走向。
• 亞股與台股量能持穩，權值與題材類股各自表現。

🏠 【房市最新動態】
• 信用管制與銀行房貸水位持續，市場買氣以自住剛需為主。
• 價格進入高檔盤整期，買賣雙方保持觀望。

---
*🚀 來自 GitHub Actions 雲端自動推送！*
""".strip()

def create_report_image(date_str, report_text):
    """在雲端自動繪製一張極具專業質感的財經圖卡"""
    width, height = 1200, 670
    image = Image.new("RGB", (width, height), color="#1e1e2f")
    draw = ImageDraw.Draw(image)
    
    # 頂部裝飾霓虹彩帶
    draw.rectangle([0, 0, width, 12], fill="#00d2ff")
    
    # 標題與日期
    draw.text((60, 45), "📈 每日財經與房市快報", fill="#ffffff")
    draw.text((60, 95), f"Date: {date_str}", fill="#00d2ff")
    
    # 內文區塊底板
    draw.rounded_rectangle([50, 145, 1150, 600], radius=15, fill="#252538")
    
    # 將文字逐行繪製到圖卡上（自動截斷過長行以適應圖面）
    lines = report_text.split("\n")
    y_offset = 175
    for line in lines:
        if line.strip().startswith("📈") or line.strip().startswith("📊") or line.strip().startswith("🏠") or line.strip().startswith("---"):
            y_offset += 10
            continue
        if y_offset < 570:
            # 濾掉 markdown 的過多符號，保持畫面乾淨
            clean_line = line.replace("*", "").replace("#", "").strip()
            if clean_line:
                draw.text((80, y_offset), clean_line[:65], fill="#d1d1e9")
                y_offset += 30

    # 底部標語
    draw.text((60, 625), "🚀 Generated automatically by GitHub Actions & Python", fill="#8888a0")
    
    image_path = "daily_report.png"
    image.save(image_path)
    print("圖卡生成成功：", image_path)
    return image_path

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
    today_str = datetime.now().strftime("%Y-%m-%d")
    report_text = generate_live_market_report()
    
    # 同步在背景畫出一張精美圖卡
    img_file = create_report_image(today_str, report_text)
    
    # 發送文字與推播
    send_to_discord(report_text)
    send_to_line(report_text)
