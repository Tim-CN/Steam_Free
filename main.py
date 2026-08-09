import os
from src.crawler import fetch_free_games
from src.supabase_client import save_games_to_supabase
from src.email_sender import send_email

def main():
    print("开始抓取 SteamDB 免费游戏...")
    games = fetch_free_games()
    print(f"抓取到 {len(games)} 个游戏")

    if not games:
        print("没有抓取到数据，退出")
        return

    # 存入 Supabase
    try:
        inserted, skipped = save_games_to_supabase(games)
        print(f"存入 Supabase: 新增 {inserted} 条，跳过 {skipped} 条（已存在）")
    except Exception as e:
        print(f"Supabase 操作失败: {e}")

    # 发送邮件（可配置是否发送全部或仅新游戏）
    send_email(games)
    print("任务完成")

if __name__ == "__main__":
    main()
