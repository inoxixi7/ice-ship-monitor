import requests
from bs4 import BeautifulSoup
import os
import sys

# ================= 配置区域 =================
# 从环境变量获取，这样更安全，代码传到 GitHub 也不会泄露 Token
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# 监控设置
TARGETS = [
    {
        "date": "2026-02-28",
        "url": "https://www.ms-aurora.com/abashiri/reserves/new.php?ym=2026-02",
        "day_check": "28"
    },
    {
        "date": "2026-03-01",
        "url": "https://www.ms-aurora.com/abashiri/reserves/new.php?ym=2026-03",
        "day_check": "1"
    }
]
# ===========================================

def send_telegram_message(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("Error: Token or Chat ID not found.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def check_site():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    AVAILABLE_SYMBOLS = ['○', '△'] 

    for target in TARGETS:
        date_str = target['date']
        target_url = target['url']
        day_to_find = target['day_check']
        
        print(f"Checking {date_str}...")
        try:
            r = requests.get(target_url, headers=headers, timeout=15)
            r.encoding = 'utf-8' 
            if r.status_code != 200: continue

            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 搜索 td (修正版逻辑)
            for cell in soup.find_all(['td', 'th']):
                cell_text = cell.get_text(strip=True)
                if cell_text.startswith(day_to_find):
                    remaining = cell_text[len(day_to_find):]
                    if remaining and remaining[0].isdigit(): continue 
                    
                    # 检查符号
                    is_available = False
                    status_symbol = ""
                    for symbol in AVAILABLE_SYMBOLS:
                        if symbol in cell_text:
                            is_available = True
                            status_symbol = symbol
                            break
                    
                    if is_available:
                        # 尝试提取链接
                        click_url = target_url
                        link_tag = cell.find('a')
                        if link_tag and link_tag.get('href'):
                            href = link_tag.get('href')
                            if not href.startswith('http'):
                                click_url = "https://www.ms-aurora.com/abashiri/reserves/" + href
                            else:
                                click_url = href

                        msg = (
                            f"🚨 **发现空位！(GitHub Action)** 🚨\n\n"
                            f"📅 日期: {date_str}\n"
                            f"ℹ️ 状态: {status_symbol}\n"
                            f"🔗 [点击立即预约]({click_url})"
                        )
                        print(f"FOUND: {date_str}")
                        send_telegram_message(msg)
                    else:
                        print(f"Not found: {date_str}")
                    break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_site()