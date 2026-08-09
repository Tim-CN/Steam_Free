import os
import requests
from datetime import datetime

# 从环境变量读取 API Key（你需要在 GitHub Secrets 中添加）
API_KEY = os.getenv("STEAMDB_API_KEY")
# Anysite 的 SteamDB 促销信息 API 端点（根据官方文档确认）
API_URL = "https://api.anysite.io/v1/steamdb/promotions"

def fetch_free_games():
    """
    通过 Anysite API 获取 SteamDB 即将免费的游戏列表
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
    if not API_KEY:
        raise ValueError(
            "STEAMDB_API_KEY 未设置！请到 https://anysite.io/ 注册并获取 API Key，"
            "然后在 GitHub Secrets 中添加 STEAMDB_API_KEY。"
        )

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }
    # 可选的查询参数，根据文档调整，例如 filter=upcoming
    params = {
        "filter": "upcoming"   # 仅获取即将到来的免费游戏
    }

    try:
        resp = requests.get(API_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"API 请求失败: {e}")

    # 根据 Anysite API 实际返回结构解析（以下为示例，请根据真实响应调整）
    # 通常返回格式：{ "status": "success", "data": [ {...}, ... ] }
    items = data.get("data", [])
    if not items:
        # 有些 API 可能直接返回列表，尝试兼容
        items = data if isinstance(data, list) else []

    games = []
    for item in items:
        # 字段名可能需要根据文档调整
        name = item.get("name") or item.get("title") or ""
        url = item.get("url") or ""
        image = item.get("image") or item.get("thumbnail") or ""
        promo = item.get("promotion_type") or item.get("type") or "Free"

        # 时间字段可能为 timestamp 或 ISO 字符串
        start_ts = item.get("start_date") or item.get("start_time")
        end_ts = item.get("end_date") or item.get("end_time")

        start_dt = parse_time(start_ts)
        end_dt = parse_time(end_ts)

        games.append({
            'name': name,
            'url': url,
            'image': image,
            'start_time': start_dt,
            'end_time': end_dt,
            'promotion_type': promo
        })

    return games

def parse_time(value):
    """尝试将各种格式的时间转换为 datetime 对象"""
    if not value:
        return None
    # 如果是整数时间戳（秒级）
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value)
        except:
            return None
    # 如果是 ISO 格式字符串
    if isinstance(value, str):
        # 尝试常见 ISO 格式
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        # 如果包含时区，尝试简单去除后处理
        if "T" in value:
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                pass
    return None
