import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def fetch_free_games():
    """
    从 https://steamdb.info/upcoming/free/ 抓取即将免费的游戏列表
    返回列表，每个元素为 dict：
    {
        'name': str,
        'url': str,            # SteamDB 页面链接
        'image': str,          # 封面图链接（可能为空）
        'start_time': datetime or None,
        'end_time': datetime or None,
        'promotion_type': str  # 例如 "Free to Keep" 等
    }
    """
    url = "https://steamdb.info/upcoming/free/"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, 'html.parser')
    # 找到表格主体（通常 class 为 'table-products'）
    table = soup.find('table', class_='table-products')
    if not table:
        # 尝试找 tbody
        table = soup.find('tbody')
    if not table:
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

        # 提取图片（可能放在 img 中）
        img_tag = row.find('img')
        image_url = img_tag.get('src') if img_tag else ""

        # 提取日期和时间（通常在第 3 和第 4 个 td）
        tds = row.find_all('td')
        if len(tds) < 4:
            continue

        # 促销类型（例如 "Free to Keep"）
        promo_type = tds[1].get_text(strip=True) if len(tds) > 1 else ""

        # 开始时间（td[2]）
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
    """解析 SteamDB 的时间格式，例如 '2026-08-10 01:00:00' 或 'Aug 10, 2026 01:00'"""
    if not text or text == '-':
        return None
    text = text.strip()
    # 尝试多种格式
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
    # 如果都失败，返回 None
    return None
