import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime
import time

def fetch_free_games():
    """
    使用 cloudscraper 绕过 Cloudflare，直接抓取 SteamDB 即将免费页面
    返回游戏列表
    """
    url = "https://steamdb.info/upcoming/free/"
    
    # 创建 cloudscraper 实例，使用真实浏览器指纹
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        },
        # 增加超时和重试
        timeout=30,
        retries=3
    )
    
    # 完整的请求头（模拟 Chrome）
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://steamdb.info/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    
    try:
        # 使用 session 保持 cookies
        session = scraper.session
        session.headers.update(headers)
        # 添加一些常用 cookies
        session.cookies.set('steamdb_lang', 'en')
        
        resp = scraper.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        raise Exception(f"SteamDB 请求失败: {e}")
    
    # 解析 HTML
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # 定位表格（SteamDB 使用 class 'table-products'）
    table = soup.find('table', class_='table-products')
    if not table:
        # 尝试直接找 tbody
        table = soup.find('tbody')
    if not table:
        # 尝试查找所有表格
        tables = soup.find_all('table')
        if tables:
            table = tables[0]  # 取第一个表格
        else:
            raise Exception("无法找到数据表格，页面结构可能已变化")
    
    rows = table.find_all('tr')
    games = []
    
    for row in rows:
        # 提取游戏名称和链接
        name_tag = row.find('a', class_='b')
        if not name_tag:
            continue
        name = name_tag.get_text(strip=True)
        relative_url = name_tag.get('href')
        full_url = f"https://steamdb.info{relative_url}" if relative_url else ""
        
        # 提取图片（可能不存在）
        img_tag = row.find('img')
        image_url = img_tag.get('src') if img_tag else ""
        
        # 提取所有 td
        tds = row.find_all('td')
        if len(tds) < 4:
            continue
        
        # 促销类型（第二个 td）
        promo_type = tds[1].get_text(strip=True) if len(tds) > 1 else "Free"
        
        # 开始和结束时间（第3、4个 td）
        start_text = tds[2].get_text(strip=True) if len(tds) > 2 else ""
        end_text = tds[3].get_text(strip=True) if len(tds) > 3 else ""
        
        start_dt = parse_steamdb_datetime(start_text)
        end_dt = parse_steamdb_datetime(end_text)
        
        games.append({
            'name': name,
            'url': full_url,
            'image': image_url,
            'start_time': start_dt,
            'end_time': end_dt,
            'promotion_type': promo_type
        })
    
    return games


def parse_steamdb_datetime(text):
    """解析 SteamDB 的时间格式"""
    if not text or text == '-':
        return None
    text = text.strip()
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%b %d, %Y %H:%M',
        '%B %d, %Y %H:%M',
        '%Y-%m-%d',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None
