"""Аналитика переходов по часам."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import LinkClick, ShortLink

MONTH_NAMES = (
    "",
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
)


def _parse_day(value: str | None) -> date:
    if not value:
        return datetime.utcnow().date()
    return date.fromisoformat(value)


def _parse_month(value: str | None) -> tuple[int, int]:
    if not value:
        now = datetime.utcnow()
        return now.year, now.month
    year_str, month_str = value.split("-", 1)
    return int(year_str), int(month_str)


def _hourly_buckets(clicks: list[tuple[int, int]]) -> list[dict]:
    counts = {hour: count for hour, count in clicks}
    points = []
    for hour in range(24):
        points.append(
            {
                "hour": hour,
                "label": f"{hour:02d}:00",
                "count": int(counts.get(hour, 0)),
            }
        )
    return points


def build_link_activity(
    db: Session,
    link: ShortLink,
    *,
    mode: str,
    date_value: str | None,
) -> dict:
    if mode == "month":
        year, month = _parse_month(date_value)
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        range_label = f"{MONTH_NAMES[month]} {year}"
        date_key = f"{year:04d}-{month:02d}"
    else:
        day = _parse_day(date_value)
        start = datetime.combine(day, datetime.min.time())
        end = start + timedelta(days=1)
        range_label = day.strftime("%d.%m.%Y")
        date_key = day.isoformat()

    rows = (
        db.query(func.extract("hour", LinkClick.clicked_at).label("hour"), func.count(LinkClick.id))
        .filter(
            LinkClick.link_id == link.id,
            LinkClick.clicked_at >= start,
            LinkClick.clicked_at < end,
        )
        .group_by("hour")
        .order_by("hour")
        .all()
    )
    points = _hourly_buckets([(int(row.hour), int(row[1])) for row in rows])
    total = sum(point["count"] for point in points)

    return {
        "mode": mode,
        "date": date_key,
        "range_label": range_label,
        "total": total,
        "points": points,
    }
