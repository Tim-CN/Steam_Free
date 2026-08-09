import requests
from datetime import datetime

def fetch_free_games():
    """
    使用 GamerPower 免费 API 获取 Steam 即将免费的游戏
    无需 API Key，完全免费
    """
    url = "https://www.gamerpower.com/api/freebies"
    params = {
        "type": "game",          # 只获取游戏（不含 DLC、皮肤等）
        "platform": "steam",     # 只筛选 Steam 平台
        "sort-by": "date"        # 按日期排序
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise Exception(f"GamerPower API 请求失败: {e}")

    if not data:
        raise Exception("GamerPower API 返回空数据，请稍后重试")

    games = []
    for item in data:
        # 只处理状态为 "Coming Soon" 或 "Active" 的游戏
        status = item.get("status", "")
        if status not in ["Coming Soon", "Active"]:
            continue

        name = item.get("title", "未知游戏")

        # 构建 SteamDB 链接（优先使用 steam_id）
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
        # 统一为友好名称
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


def parse_gamerpower_time(value):
    """解析 GamerPower 返回的 ISO 时间字符串"""
    if not value:
        return None
    try:
        # 处理毫秒部分
        if '.' in value:
            value = value.split('.')[0] + 'Z'
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None
