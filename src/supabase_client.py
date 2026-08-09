import os
from supabase import create_client, Client
from datetime import datetime

# 从环境变量读取（GitHub Actions 中会注入）
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def save_games_to_supabase(games):
    """
    将游戏列表存入 free_games 表，如果已存在相同 name 则跳过（或更新）
    这里采用简单策略：先查询是否存在，不存在则插入
    """
    supabase = get_supabase_client()
    inserted = 0
    skipped = 0

    for game in games:
        # 检查是否已存在（以 name 为准，因为可能重复）
        resp = supabase.table('free_games')\
            .select('id')\
            .eq('name', game['name'])\
            .execute()
        if resp.data:
            skipped += 1
            continue

        # 插入新记录
        data = {
            'name': game['name'],
            'url': game['url'],
            'image': game['image'],
            'start_time': game['start_time'].isoformat() if game['start_time'] else None,
            'end_time': game['end_time'].isoformat() if game['end_time'] else None,
            'promotion_type': game['promotion_type'],
            'fetched_at': datetime.now().isoformat()
        }
        try:
            supabase.table('free_games').insert(data).execute()
            inserted += 1
        except Exception as e:
            print(f"插入失败 {game['name']}: {e}")

    return inserted, skipped
