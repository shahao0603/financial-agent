import urllib.request
import json
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_GROUP_ID = os.environ.get("LINE_GROUP_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def download_font():
    """自動從開源專案下載中文字型（Noto Sans TC），確保雲端畫圖不出方框"""
    font_path = "NotoSansTC-Regular.ttf"
    if not os.path.exists(font_path):
        print("正在下載中文字型...")
        font_url = "https://github.com/google/fonts/raw/main/ofl/notosanstc/NotoSansTC-Regular.ttf"
        try:
            urllib.request.urlretrieve(font_url, font_path)
            print("中文字型下載成功！")
        except Exception as e:
            print("字型下載失敗，使用系統預設：", e)
    return font_path if os.path.exists(font_path) else None

def generate_market_report():
    today = datetime.now().strftime("%Y-%m-%d (%A)")
    
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
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
            prompt = f"請以專業金融從業人員角度，為我撰寫一份精煉的「每日財經與房市快報」（日期：{today}），包含股市總經與房市最新動態，語氣專業俐落。"
            payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as res:
                res_data = json.loads(res.read().decode("utf-8"))
                text_content = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print("AI 生成失敗，使用預設文字：", e)
            
    return text_content

def create_report_image(date_str, report_text):
    """動態繪製一張精美的財經快報資訊圖卡"""
    width, height = 1200, 670
    image = Image.new("RGB", (width, height), color="#1e1e2f")
    draw = ImageDraw.Draw(image)
    
    # 載入中文字型
    font_path = download_font()
    try:
        title_font = ImageFont.truetype(font_path, 36) if font_path else ImageFont.load_default()
        sub_font = ImageFont.truetype(font_path, 22) if font_path else ImageFont.load_default()
        body_font = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()
    except Exception:
        title_font = sub_font = body_font = ImageFont.load_default()

    # 頂部裝飾彩帶
    draw.rectangle([0, 0, width, 12], fill="#00d2ff")
    
    # 繪製標題與日期
    draw.text((60, 45), "📈 每日財經與房市快報", fill="#ffffff", font=title_font)
    draw.text((60, 95), f"Date: {date_str}", fill="#00d2ff", font=sub_font)
    
    # 內容底板
    draw.rounded_rectangle([50, 145, 1150, 600], radius=15, fill="#252538")
    
    # 將 AI 生成的文字切行畫到圖卡上
    lines = report_text.split("\n")
    y_offset = 175
    for line in lines:
        if line.strip().startswith("📈") or line.strip().startswith("📊") or line.strip().startswith("🏠") or line.strip().startswith("---"):
            y_offset += 10
            continue # 跳過過長的大標題，或特別繪製
        if y_offset < 570:
            draw.text((80, y_offset), line[:55], fill="#d1d1e9", font=body_font)
            y_offset += 32

    # 底部標語
    draw.text((60, 625), "🚀 Generated automatically by GitHub Actions & Python", fill="#8888a0", font=sub_font)
    
    image_path = "daily_report.png"
    image.save(image_path)
    return image_path

def send_to_discord(content):
    if not DISCORD_WEBHOOK_URL: return
    data = json.dumps({"content": content}).encode("utf-8")
    req = urllib.request.Request(DISCORD_WEBHOOK_URL, data=data, headers={"Content-Type": "application/json"})
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
    today_str = datetime.now().strftime("%Y-%m-%d")
    report_text = generate_market_report()
    img_file = create_report_image(today_str, report_text)
    
    # 發送文字快報
    send_to_discord(report_text)
    send_to_line(report_text)
