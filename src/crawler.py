import requests
import time
from datetime import datetime

# 主 API 源：GamerPower
GAMERPOWER_URL = "https://www.gamerpower.com/api/freebies"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.gamerpower.com/",
    "Connection": "keep-alive",
}


def fetch_free_games(max_retries=2):
    """
    尝试从 GamerPower 获取数据，如果失败则使用备用源
    """
    for attempt in range(max_retries + 1):
        try:
            games = fetch_from_gamerpower()
            if games:
                return games
        except Exception as e:
            print(f"GamerPower 尝试 {attempt+1} 失败: {e}")
            if attempt < max_retries:
                time.sleep(2)
            continue

    # 主源失败，尝试备用源
    print("主源失败，尝试备用源...")
    try:
        return fetch_from_steamdb_fallback()
    except Exception as e:
        raise Exception(f"所有数据源均失败，最后错误: {e}")


def fetch_from_gamerpower():
    """从 GamerPower API 获取数据"""
    params = {
        "type": "game",
        "platform": "steam",
        "sort-by": "date"
    }

    resp = requests.get(GAMERPOWER_URL, params=params, headers=HEADERS, timeout=15)
    
    if resp.status_code != 200:
        # 打印响应内容前 200 字符帮助调试
        preview = resp.text[:200] if resp.text else "(空响应)"
        raise Exception(f"HTTP {resp.status_code}: {preview}")

    # 尝试解析 JSON
    try:
        data = resp.json()
    except ValueError as e:
        preview = resp.text[:200] if resp.text else "(空响应)"
        raise Exception(f"JSON 解析失败 ({e}): {preview}")

    if not data:
        raise Exception("API 返回空列表")

    games = []
    for item in data:
        status = item.get("status", "")
        if status not in ["Coming Soon", "Active"]:
            continue

        name = item.get("title", "未知游戏")
        steam_id = item.get("steam_id")
        if steam_id:
            db_url = f"https://steamdb.info/app/{steam_id}/"
        else:
            db_url = item.get("open_giveaway", "")
            if not db_url:
                db_url = f"https://store.steampowered.com/app/{item.get('id', '')}"

        image_url = item.get("thumbnail", "") or item.get("image", "")
        start_dt = parse_gamerpower_time(item.get("published_date"))
        end_dt = parse_gamerpower_time(item.get("end_date"))
        promo_type = item.get("type", "Free")
        if promo_type == "Free Game":
            promo_type = "Free to Keep"

        games.append({
            'name': name,
            'url': db_url,
            'image': image_url,
            'start_time': start_dt,
            'end_time': end_dt,
            'promotion_type': promo_type
        })

    return games


def fetch_from_steamdb_fallback():
    """
    备用方案：直接爬取 SteamDB（不使用 cloudscraper，仅使用普通 requests）
    可能也会被 403，但作为最后尝试
    """
    url = "https://steamdb.info/upcoming/free/"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table', class_='table-products')
    if not table:
        table = soup.find('tbody')
    if not table:
        raise Exception("无法找到表格")
    rows = table.find_all('tr')
    games = []
    for row in rows:
        name_tag = row.find('a', class_='b')
        if not name_tag:
            continue
        name = name_tag.get_text(strip=True)
        relative_url = name_tag.get('href')
        full_url = f"https://steamdb.info{relative_url}" if relative_url else ""
        tds = row.find_all('td')
        if len(tds) < 4:
            continue
        promo_type = tds[1].get_text(strip=True) if len(tds) > 1 else "Free"
        start_text = tds[2].get_text(strip=True) if len(tds) > 2 else ""
        end_text = tds[3].get_text(strip=True) if len(tds) > 3 else ""
        start_dt = parse_steamdb_datetime(start_text)
        end_dt = parse_steamdb_datetime(end_text)
        games.append({
            'name': name,
            'url': full_url,
            'image': "",
            'start_time': start_dt,
            'end_time': end_dt,
            'promotion_type': promo_type
        })
    return games


def parse_gamerpower_time(value):
    if not value:
        return None
    try:
        if '.' in value:
            value = value.split('.')[0] + 'Z'
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None


def parse_steamdb_datetime(text):
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
