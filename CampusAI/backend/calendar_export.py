"""日历导出：把「截止日期 + 倒数日事件」生成 .ics 日历文件，供同步到手机日历。

iCalendar（RFC 5545）：all-day 事件用 DTSTART;VALUE=DATE:YYYYMMDD 表示。
复用 reminders.build_reminders() 收集未来事项（传大窗口 = 全部未来截止/事件）。
"""

from datetime import datetime

from reminders import build_reminders


# 导出时收进「所有未来事项」，不设 7 天窗口
_WINDOW_DAYS = 3650


def _ical_escape(text):
    """转义 iCalendar 文本里的特殊字符（反斜杠 / 分号 / 逗号 / 换行）。"""
    if not text:
        return ""
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _date_value(iso):
    """YYYY-MM-DD → YYYYMMDD；非法日期返回 None。"""
    try:
        return datetime.strptime(str(iso)[:10], "%Y-%m-%d").strftime("%Y%m%d")
    except (ValueError, TypeError):
        return None


def build_calendar():
    """生成 iCalendar 内容字符串（\r\n 行尾，UTF-8）。"""
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Personal Magazine//CampusAI//CN",
        "CALSCALE:GREGORIAN",
    ]

    for r in build_reminders(deadline_window=_WINDOW_DAYS, event_window=_WINDOW_DAYS):
        d = _date_value(r.get("date"))
        if not d:
            continue
        kind = "截止" if r.get("type") == "deadline" else "事件"
        summary = f"[{kind}] {r.get('title', '')}"
        description = r.get("action", "") or ""
        # UID 需稳定，避免同一事项反复导入时重复
        uid = r.get("url") or f"event:{r.get('date')}:{r.get('title', '')}"

        lines += [
            "BEGIN:VEVENT",
            f"UID:{_ical_escape(uid)}",
            f"DTSTAMP:{now}",
            f"DTSTART;VALUE=DATE:{d}",
            f"SUMMARY:{_ical_escape(summary)}",
        ]
        if description:
            lines.append(f"DESCRIPTION:{_ical_escape(description)}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
