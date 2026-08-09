import requests
from datetime import datetime

def fetch_free_games():
    """
    通过 GamerPower 免费 API 获取即将免费的游戏列表
    仅筛选 Steam 平台的游戏
    返回列表，每个元素为 dict：
    {
        'name': str,
        'url': str,
        'image': str,
        'start_time': datetime or None,
        'end_time': datetime or None,
        'promotion_type': str
    }
    """
    # GamerPower 免费 API 端点，无需 API Key
    url = "https://www.gamerpower.com/api/freebies"
    params = {
        "type": "game",        # 只获取游戏类型（不包含 DLC、皮肤等）
        "platform": "steam",   # 只获取 Steam 平台的游戏
        "sort-by": "date"      # 按日期排序
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"API 请求失败: {e}")

    if not data:
        raise Exception("API 返回空数据，请稍后重试")

    games = []
    for item in data:
        # 只处理即将到来的免费游戏（status 为 'Coming Soon' 或 'Active'）
        status = item.get("status", "")
        if status not in ["Coming Soon", "Active"]:
            continue

        # 提取游戏信息
        name = item.get("title", "未知游戏")
        # GamerPower 返回的是 giveaway 页面，但我们构建 SteamDB 链接
        # 如果 item 有 open_giveaway 字段，使用它，否则构建 SteamDB 搜索链接
        db_url = item.get("open_giveaway", "")
        if not db_url:
            # 如果 API 返回了 steam_id，可以构建 SteamDB 链接
            steam_id = item.get("steam_id", "")
            if steam_id:
                db_url = f"https://steamdb.info/app/{steam_id}/"
            else:
                db_url = f"https://store.steampowered.com/app/{item.get('id', '')}"

        # 图片 URL
        image_url = item.get("thumbnail", "")
        if not image_url:
            image_url = item.get("image", "")

        # 解析时间
        start_dt = parse_gamerpower_time(item.get("published_date"))
        end_dt = parse_gamerpower_time(item.get("end_date"))

        # 促销类型
        giveaway_type = item.get("type", "Free")
        if giveaway_type == "Free Game":
            promo_type = "Free to Keep"
        else:
            promo_type = giveaway_type

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
    """解析 GamerPower API 返回的时间格式"""
    if not value:
        return None
    # GamerPower 返回的是 ISO 格式: 2026-08-10T00:00:00.000Z
    try:
        # 移除毫秒部分处理
        if '.' in value:
            value = value.split('.')[0] + 'Z'
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        # 尝试其他格式
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
