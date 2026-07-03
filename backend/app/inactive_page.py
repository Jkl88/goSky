"""Красивая HTML-страница для неактивных коротких ссылок."""

from __future__ import annotations

from html import escape

from .link_logic import InactiveKind

_PHRASES: dict[InactiveKind, list[str]] = {
    "disabled": [
        "Владелец выключил свет. Ссылка дремлет под одеялом.",
        "Эта ссылка в отпуске без доступа к интернету.",
        "Стоп-кран сработал. Дальше не пускаем.",
        "Ссылка на паузе — попейте чай и вернитесь позже.",
        "Здесь было что-то интересное, но кто-то нажал «выкл».",
        "Ссылка ушла в нирвану. Омм.",
        "Как выключенный телевизор — вроде есть, но ничего не показывает.",
    ],
    "expired": [
        "Срок годности истёк. Ссылка превратилась в тыкву.",
        "Эта ссылка ушла в закат вместе с TTL.",
        "Время вышло — даже у коротких ссылок бывают дедлайны.",
        "Ссылка состарилась быстрее, чем вы успели кликнуть.",
        "Песочные часы пусты. Путь закрыт.",
        "Эта ссылка уже в архиве истории интернета.",
        "TTL сказал «пока» — и ссылка послушно ушла.",
    ],
    "max_clicks": [
        "Лимит переходов исчерпан. Ссылка устала от популярности.",
        "Слишком много гостей — дверь закрыта на обед.",
        "Квота кликов закончилась. VIP-проход закрыт.",
        "Эта ссылка набрала свой максимум славы.",
        "Счётчик дошёл до нуля. Билеты распроданы.",
        "Ссылка перегрелась от хайпа и ушла на боковую.",
        "Все места заняты. Приходите на следующий сеанс.",
    ],
}

_SUBTITLES: dict[InactiveKind, str] = {
    "disabled": "Ссылка отключена",
    "expired": "Срок действия истёк",
    "max_clicks": "Лимит переходов исчерпан",
}

_EMOJI: dict[InactiveKind, str] = {
    "disabled": "😴",
    "expired": "⏳",
    "max_clicks": "🚫",
}

INACTIVE_PHRASE_COOKIE_PREFIX = "gi_"


def phrase_cookie_name(slug: str) -> str:
    return f"{INACTIVE_PHRASE_COOKIE_PREFIX}{slug}"


def pick_phrase(kind: InactiveKind, phrase_index: int) -> tuple[str, int]:
    phrases = _PHRASES.get(kind) or _PHRASES["disabled"]
    idx = phrase_index % len(phrases)
    return phrases[idx], (phrase_index + 1) % len(phrases)


def render_inactive_page(
    *,
    slug: str,
    kind: InactiveKind,
    phrase: str,
    home_url: str,
    show_home_button: bool,
) -> str:
    subtitle = _SUBTITLES.get(kind, "Ссылка недоступна")
    emoji = _EMOJI.get(kind, "🔗")
    safe_slug = escape(slug)
    safe_phrase = escape(phrase)
    safe_subtitle = escape(subtitle)
    safe_home = escape(home_url)
    home_btn = f'<a class="btn" href="{safe_home}">На главную</a>' if show_home_button else ""

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>goSky — {safe_subtitle}</title>
  <style>
    :root {{
      color-scheme: dark light;
      --bg1: #0b1220;
      --bg2: #162033;
      --card: rgba(255,255,255,.06);
      --text: #e8eefc;
      --muted: #9aa8c7;
      --accent: #5b8cff;
      --accent2: #7c5cff;
    }}
    @media (prefers-color-scheme: light) {{
      :root {{
        --bg1: #eef3ff;
        --bg2: #dce6ff;
        --card: rgba(255,255,255,.75);
        --text: #15203a;
        --muted: #5a6b8a;
      }}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      background:
        radial-gradient(1200px 600px at 10% -10%, rgba(91,140,255,.25), transparent 60%),
        radial-gradient(900px 500px at 100% 0%, rgba(124,92,255,.2), transparent 55%),
        linear-gradient(160deg, var(--bg1), var(--bg2));
      color: var(--text);
      padding: 24px;
    }}
    .card {{
      width: min(520px, 100%);
      background: var(--card);
      border: 1px solid rgba(255,255,255,.12);
      border-radius: 24px;
      padding: 32px 28px;
      text-align: center;
      backdrop-filter: blur(12px);
      box-shadow: 0 24px 60px rgba(0,0,0,.25);
      animation: float-in .5s ease-out;
    }}
    @keyframes float-in {{
      from {{ opacity: 0; transform: translateY(12px) scale(.98); }}
      to {{ opacity: 1; transform: none; }}
    }}
    .emoji {{ font-size: 56px; line-height: 1; margin-bottom: 12px; }}
    .brand {{
      font-size: 13px;
      letter-spacing: .12em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 8px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(22px, 4vw, 28px);
      font-weight: 700;
    }}
    .slug {{
      display: inline-block;
      margin: 0 0 20px;
      padding: 4px 10px;
      border-radius: 999px;
      background: rgba(91,140,255,.15);
      color: var(--accent);
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 14px;
    }}
    .phrase {{
      margin: 0 0 24px;
      font-size: 18px;
      line-height: 1.5;
      color: var(--text);
    }}
    .btn {{
      display: inline-block;
      padding: 12px 22px;
      border-radius: 14px;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      color: #fff;
      text-decoration: none;
      font-weight: 600;
      transition: transform .15s ease, box-shadow .15s ease;
      box-shadow: 0 8px 24px rgba(91,140,255,.35);
    }}
    .btn:hover {{ transform: translateY(-1px); }}
    .footer {{
      margin-top: 20px;
      font-size: 12px;
      color: var(--muted);
    }}
  </style>
</head>
<body>
  <main class="card">
    <div class="emoji">{emoji}</div>
    <div class="brand">goSky</div>
    <h1>{safe_subtitle}</h1>
    <div class="slug">/{safe_slug}</div>
    <p class="phrase">{safe_phrase}</p>
    {home_btn}
    <div class="footer">SkyKraft · go.skykraft.su</div>
  </main>
</body>
</html>"""
