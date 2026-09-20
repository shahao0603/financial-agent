import urllib.request
import json
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_GROUP_ID = os.environ.get("LINE_GROUP_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def generate_market_report():
    today = datetime.now().strftime("%Y-%m-%d (%A)")
    
    # 預設保底文字
    text_content = f"""
📈 【每日財經與房市快報】 - {today}

📊 【股市與總經要聞】
• 美國與國際：美股主要指數高檔震盪，市場緊盯總經與聯準會動向。
• 台股動態：成交量維持水準，權值股與強勢族群輪動快速。

🏠 【房市最新動態】
• 貸款政策：銀行房貸水位與信用管制持續，自住買氣為主力。
• 價格格局：市場進入高檔盤整，買賣雙方拉鋸中。

---
*🚀 來自 GitHub Actions 雲端 AI 機器人圖文自動推送！*
""".strip()

    if GEMINI_API_KEY:
        # 使用正確穩定的 Gemini 2.5 Flash API  endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        prompt = f"""
        請以專業金融與房市從業人員的視角，為我撰寫一份簡明扼要的「每日財經與房市快報」（日期：{today}）。
        排版包含股市總經與房市最新動態，語氣專業俐落。
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
        except Exception as e:
            print("AI 生成失敗，使用預設文字：", e)
            
    return text_content

def create_report_image(date_str, report_text):
    """使用內建字型繪製質感資訊圖卡，確保絕對不會下載失敗"""
    width, height = 1200, 670
    image = Image.new("RGB", (width, height), color="#1e1e2f")
    draw = ImageDraw.Draw(image)
    
    # 使用 Pillow 內建字型，免去下載外部檔案的風險
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    # 頂部裝飾彩帶
    draw.rectangle([0, 0, width, 12], fill="#00d2ff")
    
    # 標題與日期
    draw.text((60, 45), "📈 每日財經與房市快報", fill="#ffffff")
    draw.text((60, 95), f"Date: {date_str}", fill="#00d2ff")
    
    # 內容底板
    draw.rounded_rectangle([50, 145, 1150, 600], radius=15, fill="#252538")
    
    # 將文字畫到圖卡上
    lines = report_text.split("\n")
    y_offset = 175
    for line in lines:
        if line.strip().startswith("📈") or line.strip().startswith("📊") or line.strip().startswith("🏠") or line.strip().startswith("---"):
            y_offset += 10
            continue
        if y_offset < 570:
            draw.text((80, y_offset), line[:65], fill="#d1d1e9")
            y_offset += 28

    # 底部標語
    draw.text((60, 625), "🚀 Generated automatically by GitHub Actions & Python", fill="#8888a0")
    
    image_path = "daily_report.png"
    image.save(image_path)
    return image_path

def send_to_discord(content):
    if not DISCORD_WEBHOOK_URL: 
        print("未設定 Discord Webhook")
        return
        
    data = json.dumps({"content": content}).encode("utf-8")
    # 加上標準 User-Agent 避免被 Discord 擋下 (403 Forbidden)
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
    if not LINE_TOKEN or not LINE_GROUP_ID: 
        print("未設定 LINE Token 或 Group ID")
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
        with urllib.request.urlopen(req) as res: 
            print("LINE 發送成功！狀態碼：", res.status)
    except Exception as e: 
        print("LINE 發送失敗：", e)

if __name__ == "__main__":
    today_str = datetime.now().strftime("%Y-%m-%d")
    report_text = generate_market_report()
    img_file = create_report_image(today_str, report_text)
    
    send_to_discord(report_text)
    send_to_line(report_text)
