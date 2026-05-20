from playwright.sync_api import sync_playwright
import requests
import os
import time

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'

# 多备用登录域名
LOGIN_DOMAINS = [
    "https://ikuuu.win/auth/login",
    "https://ikuuu.fyi/auth/login",
    "https://ikuuu.me/auth/login",
    "https://ikuuu.live/auth/login"
]
CHECKIN_DOMAINS = [
    "https://ikuuu.win/user/checkin",
    "https://ikuuu.fyi/user/checkin",
    "https://ikuuu.me/user/checkin",
    "https://ikuuu.live/user/checkin"
]

def mask_email(email):
    if '@' not in email:
        return email
    name, domain = email.split('@', 1)
    if len(name) <= 1:
        masked = name
    elif len(name) == 2:
        masked = name[0] + '*'
    else:
        masked = name[0] + '*' * (len(name)-2) + name[-1]
    return f'{masked}@{domain}'

def get_valid_url(url_list):
    for url in url_list:
        try:
            requests.head(url,timeout=3)
            return url
        except:
            continue
    return url_list[0]

def playwright_login(email, passwd):
    safe_email = mask_email(email)
    login_url = get_valid_url(LOGIN_DOMAINS)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(user_agent=USER_AGENT, viewport={"width":1280,"height":800}, locale="zh-CN")
        context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
        page = context.new_page()
        page.goto(login_url, wait_until='networkidle')
        page.fill('#email', email)
        page.fill('#password', passwd)
        try:
            page.click('.geetest_btn_click', timeout=5000)
        except:
            pass
        time.sleep(2)
        page.click('button[type="submit"]')
        time.sleep(5)
        cookies = context.cookies()
        browser.close()
        return cookies

def checkin_one_account(email, passwd):
    safe_email = mask_email(email)
    check_url = get_valid_url(CHECKIN_DOMAINS)
    header = {'origin':'https://ikuuu.win','user-agent':USER_AGENT}
    try:
        pw_cookies = playwright_login(email, passwd)
        if not pw_cookies:
            raise Exception("获取Cookie失败")
        session = requests.session()
        for c in pw_cookies:
            if c.get('name') and c.get('value'):
                session.cookies.set(c['name'], c['value'])
        res = session.post(check_url, headers=header, timeout=20).json()
        return f"{safe_email} → {res.get('msg','未知状态')}"
    except Exception as e:
        return f"{safe_email} → 异常：{str(e)}"

def handler():
    accounts_str = os.environ.get("ACCOUNTS","")
    if not accounts_str:
        return "⚠️ 未配置账号信息"
    accounts = []
    for line in accounts_str.strip().splitlines():
        if line and ':' in line:
            e,p = line.split(':',1)
            accounts.append((e.strip(),p.strip()))
    if not accounts:
        return "⚠️ 无有效账号"
    res_list = []
    for email,pwd in accounts:
        res_list.append(checkin_one_account(email,pwd))
    return "\n".join(res_list)

if __name__ == "__main__":
    print(handler())
