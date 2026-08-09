import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECEIVER = os.getenv("RECEIVER_EMAIL")

def send_email(games):
    """
    将游戏列表以 HTML 表格形式发送邮件
    """
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, RECEIVER]):
        raise ValueError("邮件环境变量未完全设置")

    subject = f"Steam 即将免费游戏 - {datetime.now().strftime('%Y-%m-%d')}"

    # 构建 HTML 正文
    html_parts = [
        "<html><head><style>",
        "table { border-collapse: collapse; width: 100%; }",
        "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
        "th { background-color: #f2f2f2; }",
        "img { max-width: 100px; max-height: 60px; }",
        "</style></head><body>",
        f"<h2>今日 Steam 即将免费游戏（{len(games)} 个）</h2>",
        "<table><tr><th>游戏名</th><th>促销类型</th><th>开始时间</th><th>结束时间</th><th>链接</th></tr>"
    ]

    for g in games:
        name = g.get('name', '')
        promo = g.get('promotion_type', '')
        start = g['start_time'].strftime('%Y-%m-%d %H:%M') if g.get('start_time') else '-'
        end = g['end_time'].strftime('%Y-%m-%d %H:%M') if g.get('end_time') else '-'
        url = g.get('url', '#')
        html_parts.append(
            f"<tr><td>{name}</td><td>{promo}</td><td>{start}</td><td>{end}</td>"
            f"<td><a href='{url}'>查看</a></td></tr>"
        )

    html_parts.append("</table></body></html>")
    html_content = "".join(html_parts)

    # 构建邮件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = RECEIVER

    part = MIMEText(html_content, 'html')
    msg.attach(part)

    # 发送
    try:
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, [RECEIVER], msg.as_string())
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, [RECEIVER], msg.as_string())
        print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败: {e}")
        raise
