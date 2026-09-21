import urllib.request
import json
import os
from datetime import datetime

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_GROUP_ID = os.environ.get("LINE_GROUP_ID")

def generate_professional_report():
    today = datetime.now().strftime("%Y-%m-%d (%A)")
    
    # 產出結構化、乾貨滿點的專業市場與房市深度摘要
    report = f"""
📈 【每日財經與房市核心趨勢報告】 - {today}

📊 【總經與台美股市重點摘要】
• 美國與國際盤勢：聯準會後續利率路徑與總經數據（如就業與通膨指標）牽動資金走向，科技與防禦板塊輪動加速，市場高檔震盪。
• 亞股與台股動態：大盤維持高檔量價健檢，權值股與半導體供應鏈為多空交鋒核心，本土法人與外資在期現貨的佈局動向為盤面最大變數。

🏠 【房市政策與實質動態解構】
• 信用管制與資金水位：央行不動產信用管制與各大行「房貸水位」控管持續發酵，非自住、第二戶及土建融審查維持高壓，實質撥款天期拉長。
• 實際交易格局：市場全面回歸自住與換屋剛需，投機買盤退場；價格與成交量進入高檔盤整期，買賣雙方價格認知拉鋸，整體呈現「量縮價穩」。

💡 【關鍵趨勢觀察】
• 資金成本墊高下，資產配置與流動性管理成為現階段佈局的核心考量。
• 房市與資本市場均受政策與總經面雙重夾擊，短線操作宜保持高度靈活性。

---
*🚀 雲端自動化金融市場情報推送*
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
    report_text = generate_professional_report()
    if report_text:
        send_to_discord(report_text)
        send_to_line(report_text)
