import requests
from bs4 import BeautifulSoup
import os
import sys

# ================= 配置区域 =================
# 尝试从环境变量获取 (GitHub Actions 模式)
# 如果本地运行没有配置环境变量，请手动填入你的 Token 和 ID 用于测试
BOT_TOKEN = os.environ.get("BOT_TOKEN") or "你的_BOT_TOKEN_在这里(本地测试用)"
CHAT_ID = os.environ.get("CHAT_ID") or "你的_CHAT_ID_在这里(本地测试用)"

# 监控设置
TARGETS = [
    {
        "date": "2026-02-28",
        "url": "https://www.ms-aurora.com/abashiri/reserves/new.php?ym=2026-02",
        "day_check": "28"
    }
]
# ===========================================

def send_telegram_message(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Error: Token or Chat ID not found.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        print(f"Telegram 推送状态: {resp.status_code}")
    except Exception as e:
        print(f"Telegram Error: {e}")

def check_site():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    # 正常模式找这俩，测试模式我们反着来
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
            
            for cell in soup.find_all(['td', 'th']):
                cell_text = cell.get_text(strip=True)
                if cell_text.startswith(day_to_find):
                    remaining = cell_text[len(day_to_find):]
                    if remaining and remaining[0].isdigit(): continue 
                    
                    # === 判定逻辑 ===
                    is_available = False
                    status_symbol = "满/×" # 默认假设是满的

                    for symbol in AVAILABLE_SYMBOLS:
                        if symbol in cell_text:
                            is_available = True
                            status_symbol = symbol
                            break
                    
                    # =========================================
                    # 👇【反转逻辑核心】👇
                    # 只要没票 (not is_available)，就发通知！
                    # =========================================
                    if not is_available:
                        msg = (
                            f"🧪 **GitHub Actions 测试成功** 🧪\n\n"
                            f"我成功访问了网站，并找到了日期！\n"
                            f"📅 日期: {date_str}\n"
                            f"👀 实际看到的状态: `{cell_text}`\n"
                            f"✅ **这证明你的自动监控流水线已经通了！**"
                        )
                        print(f"TEST TRIGGER: Found {date_str} with status {cell_text}")
                        send_telegram_message(msg)
                    else:
                        print(f"竟然有票？状态是: {status_symbol}")
                    
                    # 找到一个就退出，避免发多条
                    return 

        except Exception as e:
            print(f"Error: {e}")
            # 如果报错了，也发个 Telegram 告诉你报错了，方便调试
            send_telegram_message(f"❌ 脚本运行出错: {str(e)}")

if __name__ == "__main__":
    check_site()