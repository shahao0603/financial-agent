import hashlib
import html
import urllib.error
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Taipei")
DB_URL = os.environ["SUPABASE_URL"].strip().rstrip("/")
expected_host = "kzramekpvgrrekypayey.supabase.co"
parsed_url = urllib.parse.urlparse(DB_URL)
if parsed_url.scheme != "https" or parsed_url.hostname != expected_host or parsed_url.path not in ("", "/"):
    raise RuntimeError("SUPABASE_URL is invalid. Set the GitHub Secret to https://" + expected_host + " (no quotes, paths or spaces).")
DB_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
DISCORD = os.environ["DISCORD_WEBHOOK_URL"]
LINE_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_GROUP = os.environ["LINE_GROUP_ID"]
LOOKBACK_HOURS = 48
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()

def db_request(method, table, params="", payload=None):
    url = f"{DB_URL}/rest/v1/{table}" + (f"?{params}" if params else "")
    headers = {"apikey": DB_KEY, "Authorization": f"Bearer {DB_KEY}",
               "Content-Type": "application/json", "Prefer": "return=representation"}
    data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as response:
        body = response.read()
        return json.loads(body) if body else []

def normalize(title):
    title = re.sub(r"\s*[-－|｜]\s*[^-－|｜]{1,25}$", "", title)
    title = re.sub(r"快訊|即時|最新|重磅|獨家", "", title)
    return re.sub(r"[^\w\u4e00-\u9fff]", "", title.lower())

def fingerprint(title):
    return hashlib.sha256(normalize(title).encode()).hexdigest()

def fetch_news(query, category, limit=25):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({
        "q": query, "hl": "zh-TW", "gl": "TW", "ceid": "TW:zh-Hant"})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as response:
        root = ET.fromstring(response.read())
    result = []
    for item in root.findall(".//item")[:limit]:
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        description = re.sub(r"<[^>]+>", " ", html.unescape(item.findtext("description", "")))[:600]
        date = item.findtext("pubDate", "")
        if not title or not date:
            continue
        try:
            published = parsedate_to_datetime(date).astimezone(timezone.utc)
        except (TypeError, ValueError):
            continue
        result.append({"title": title, "url": link, "category": category,
                       "published_at": published.isoformat(), "description": description,
                       "normalized_title": normalize(title),
                       "fingerprint": fingerprint(title)})
    return result

def duplicate(item, seen):
    for old in seen:
        if item["fingerprint"] == old.get("fingerprint"):
            return True
        if item["url"] and item["url"] == old.get("url"):
            return True
        a, b = item["normalized_title"], old.get("normalized_title", "")
        if a and b and SequenceMatcher(None, a, b).ratio() >= 0.84:
            return True
    return False

def summarize_items(items):
    if not GEMINI_KEY:
        raise RuntimeError("Gemini API key missing")
    sources = [{"id": i, "title": x["title"], "description": x["description"]}
               for i, x in enumerate(items)]
    prompt = ("你是繁體中文財經編輯。只能根據RSS標題與摘要，不能假裝讀過全文，"
              "不得杜撰數字、事實或影響。每則寫一句30至55字的重點整理，不能只是改寫標題。"
              "資訊不足就寫「RSS資訊不足，請閱讀原文」。"
              "只輸出JSON陣列，每項包含整數id和字串summary，所有id都要回覆。資料："
              + json.dumps(sources, ensure_ascii=False))
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           "gemini-2.5-flash:generateContent?key=" + urllib.parse.quote(GEMINI_KEY))
    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                       "generationConfig": {"temperature": 0.1,
                                            "responseMimeType": "application/json"}}).encode()
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=35) as resp:
        answer = json.load(resp)
    parsed = json.loads(answer["candidates"][0]["content"]["parts"][0]["text"])
    mapping = {entry["id"]: entry["summary"].strip() for entry in parsed
               if isinstance(entry, dict) and isinstance(entry.get("id"), int)
               and isinstance(entry.get("summary"), str)}
    if len(mapping) != len(items):
        raise ValueError("Incomplete Gemini summaries")
    return [mapping[i][:110] for i in range(len(items))]


def push_discord(message):
    # Never print the webhook URL: it contains a secret token.
    if not DISCORD.startswith("https://discord.com/api/webhooks/"):
        raise RuntimeError("Discord webhook URL format is invalid")
    data = json.dumps({"content": message}, ensure_ascii=False).encode()
    req = urllib.request.Request(DISCORD, data=data, headers={
        "Content-Type": "application/json",
        "User-Agent": "FinanceAgent/1.0 (+https://github.com/shahao0603/financial-agent)",
        "Accept": "application/json",
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.status in (200, 204)
    except urllib.error.HTTPError as exc:
        body = exc.read(600).decode("utf-8", errors="replace")
        # Discord's error body may contain useful codes; never log the URL or token.
        print(f"Discord HTTP status={exc.code}; response={body}")
        raise RuntimeError(f"Discord HTTP {exc.code}") from None

def push_line(message):
    data = json.dumps({"to": LINE_GROUP, "messages": [{"type": "text", "text": message}]},
                      ensure_ascii=False).encode()
    req = urllib.request.Request("https://api.line.me/v2/bot/message/push", data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.status == 200

def main():
    now = datetime.now(TZ)
    # Scheduled retries run every 10 minutes; one report per Taiwan weekday slot.
    requested_slot = os.environ.get("DELIVERY_SLOT", "").strip().lower()
    if requested_slot == "test":
        print("Scheduler test received; no news sent.")
        return
    scheduled = os.environ.get("GITHUB_EVENT_NAME") == "schedule" or requested_slot in ("morning", "evening")
    slot = requested_slot if requested_slot in ("morning", "evening") else ("morning" if 8 <= now.hour < 10 else "evening" if 17 <= now.hour < 19 else None)
    if scheduled and (now.weekday() >= 5 or slot is None or (slot == "morning" and not 8 <= now.hour < 10) or (slot == "evening" and not 17 <= now.hour < 19)):
        print(f"Scheduled run skipped outside weekday 08-10/17-19 Taiwan time: {now:%Y-%m-%d %H:%M}")
        return
    slot_key = f"{now:%Y-%m-%d}:{slot}" if scheduled else None
    if slot_key:
        existing = db_request("GET", "news_delivery_slots", urllib.parse.urlencode({
            "select": "slot_key", "slot_key": f"eq.{slot_key}"}))
        if existing:
            print(f"Already claimed slot {slot_key}; skip duplicate.")
            return
    cutoff = (now - timedelta(hours=LOOKBACK_HOURS)).astimezone(timezone.utc).isoformat()
    # Fail closed: never send unfiltered news if the database is unavailable.
    seen = db_request("GET", "news_memory",
                      urllib.parse.urlencode({"select": "title,url,normalized_title,fingerprint",
                                              "reported_at": f"gte.{cutoff}", "limit": "1000"}))
    searches = [
        ("美股 台股 總經 when:2d", "市場"),
        ("房貸 央行 房市 信用管制 when:2d", "房市"),
    ]
    chosen = []
    for query, category in searches:
        try:
            candidates = fetch_news(query, category)
        except Exception as exc:
            print(f"RSS error {category}: {exc}")
            continue
        count = 0
        for item in candidates:
            if count >= 4:
                break
            published = datetime.fromisoformat(item["published_at"]).astimezone(TZ)
            if published < now - timedelta(hours=24) or published > now + timedelta(minutes=10):
                continue
            if duplicate(item, seen + chosen):
                continue
            chosen.append(item)
            count += 1
    if not chosen:
        print("No new articles; nothing sent.")
        return
    heading = "早盤重點快報" if now.hour < 12 else "晚盤趨勢總結"
    try:
        summaries = summarize_items(chosen)
    except Exception as exc:
        print(f"Summary unavailable: {type(exc).__name__}")
        raise RuntimeError("Gemini summary unavailable; news not sent") from exc
    if any("資訊不足" in summary for summary in summaries):
        raise RuntimeError("Insufficient news summaries; nothing sent")
    lines = [f"📈 【每日財經與房市{heading}】 {now:%Y-%m-%d %H:%M}"]
    for category in ("市場", "房市"):
        items = [x for x in chosen if x["category"] == category]
        if items:
            lines.append(f"\n{'📊' if category == '市場' else '🏠'} 【{category}】")
            for x in items:
                lines.append(f"• {summaries[chosen.index(x)]}\n  原文：{x['url']}")
    report = "\n".join(lines)
    if len(report) > 1900:
        report = "\n".join([lines[0]] + [f"• {summaries[i][:65]}\n{x['url']}" for i, x in enumerate(chosen[:6])])
    if len(report) > 1900:
        report = report[:1890] + "…"
    # Atomic unique-key claim prevents duplicate reports from overlapping scheduled runs.
    if slot_key:
        try:
            db_request("POST", "news_delivery_slots", payload={"slot_key": slot_key})
        except urllib.error.HTTPError as exc:
            if exc.code == 409:
                print(f"Slot {slot_key} already claimed; skip duplicate.")
                return
            raise
    # Save before sending to avoid repeat pushes after partial delivery.
    # If a delivery fails, the log shows the error; manual recovery is required.
    for item in chosen:
        db_request("POST", "news_memory", payload={
            "title": item["title"], "normalized_title": item["normalized_title"],
            "url": item["url"], "category": item["category"],
            "published_at": item["published_at"], "fingerprint": item["fingerprint"]})
    failures = []
    for name, sender in (("Discord", push_discord), ("LINE", push_line)):
        try:
            if not sender(report):
                failures.append(name)
        except Exception as exc:
            print(f"{name} failed: {exc}")
            failures.append(name)
    if failures:
        raise RuntimeError("Push failed: " + ", ".join(failures))
    print(f"Sent {len(chosen)} new articles.")

if __name__ == "__main__":
    main()
