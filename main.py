import os
import sys
from datetime import datetime
from src.crawler import fetch_free_games
from src.supabase_client import save_games_to_supabase
from src.email_sender import send_email

def main():
    print("=" * 60)
    print(f"Steam 免费游戏抓取任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 抓取数据
    print("\n[1/3] 正在从 GamerPower API 获取免费游戏数据...")
    try:
        games = fetch_free_games()
        print(f"✅ 成功抓取到 {len(games)} 个即将免费的游戏")
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        sys.exit(1)

    if not games:
        print("⚠️  没有获取到任何游戏数据，任务结束")
        return

    # 打印前几个游戏摘要
    print("\n📋 游戏摘要（前5个）：")
    for idx, g in enumerate(games[:5], 1):
        start = g['start_time'].strftime('%Y-%m-%d %H:%M') if g.get('start_time') else '未知'
        print(f"  {idx}. {g['name']} | {g['promotion_type']} | 开始: {start}")
    if len(games) > 5:
        print(f"  ... 还有 {len(games)-5} 个游戏")

    # 2. 存入 Supabase
    print("\n[2/3] 正在存入 Supabase 数据库...")
    try:
        inserted, skipped = save_games_to_supabase(games)
        print(f"✅ 存入完成：新增 {inserted} 条，跳过 {skipped} 条（已存在）")
    except Exception as e:
        print(f"❌ Supabase 操作失败: {e}")
        # 继续执行邮件发送，不中断

    # 3. 发送邮件
    print("\n[3/3] 正在发送邮件通知...")
    try:
        send_email(games)
        print("✅ 邮件发送成功")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("🎉 所有任务完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
