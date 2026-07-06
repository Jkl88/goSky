"""HTML-страница ввода пароля для защищённого редиректа и /vq."""

from __future__ import annotations

from html import escape

PasswordContext = str  # "redirect" | "view"

PASSWORD_PHRASE_COOKIE_PREFIX = "gpp_"

_REDIRECT_PHRASES = [
    "За дверью что-то интересное — но сначала пароль.",
    "Секретный проход. Шёпотом: пароль.",
    "Ссылка в режиме «только для своих». Вы почти свой.",
    "Замок щёлкнул. Ключ — в вашей голове.",
    "Дальше только с паролем. Без спойлеров.",
    "VIP-зона начинается после этой формы.",
    "Пароль — и магия сработает.",
]

_VIEW_PHRASES = [
    "QR-код и детали спрятаны за замком.",
    "Страница просмотра под охраной. Пароль в студию!",
    "Заглянуть можно, но сначала — секретное слово.",
    "Превью ссылки для избранных. Вы в списке?",
    "Пароль откроет QR и подробности ссылки.",
    "Здесь не пускают без пароля — даже на /vq.",
    "Один пароль — и вы увидите всё о ссылке.",
]

_CONTEXT_PHRASES: dict[PasswordContext, list[str]] = {
    "redirect": _REDIRECT_PHRASES,
    "view": _VIEW_PHRASES,
}

_SUBMIT_LABELS: dict[PasswordContext, str] = {
    "redirect": "Открыть ссылку",
    "view": "Открыть страницу",
}


def redirect_password_cookie_name(slug: str) -> str:
    return f"gp_{slug}"


def password_phrase_cookie_name(slug: str, context: PasswordContext) -> str:
    return f"{PASSWORD_PHRASE_COOKIE_PREFIX}{context}_{slug}"


def pick_password_phrase(context: PasswordContext, phrase_index: int) -> tuple[str, int]:
    phrases = _CONTEXT_PHRASES.get(context) or _REDIRECT_PHRASES
    idx = phrase_index % len(phrases)
    return phrases[idx], (phrase_index + 1) % len(phrases)


def render_password_page(
    *,
    slug: str,
    title: str | None,
    phrase: str,
    form_action: str,
    context: PasswordContext = "redirect",
    error: str | None = None,
    hidden_fields: dict[str, str] | None = None,
) -> str:
    safe_slug = escape(slug)
    safe_title = escape(title or slug)
    safe_phrase = escape(phrase)
    safe_action = escape(form_action, quote=True)
    safe_error = escape(error) if error else ""
    submit_label = _SUBMIT_LABELS.get(context, "Открыть")
    error_block = f'<p class="error">{safe_error}</p>' if error else ""
    hidden_html = ""
    for key, value in (hidden_fields or {}).items():
        hidden_html += f'<input type="hidden" name="{escape(key)}" value="{escape(value)}" />\n'

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>goSky — доступ по паролю</title>
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
      --error: #ff6b8a;
    }}
    @media (prefers-color-scheme: light) {{
      :root {{
        --bg1: #eef3ff;
        --bg2: #dce6ff;
        --card: rgba(255,255,255,.82);
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
      width: min(420px, 100%);
      background: var(--card);
      border: 1px solid rgba(255,255,255,.12);
      border-radius: 24px;
      padding: 32px 28px;
      text-align: center;
      backdrop-filter: blur(12px);
      box-shadow: 0 24px 60px rgba(0,0,0,.25);
      animation: float-in .45s ease-out;
    }}
    @keyframes float-in {{
      from {{ opacity: 0; transform: translateY(10px); }}
      to {{ opacity: 1; transform: none; }}
    }}
    .lock {{ font-size: 48px; margin-bottom: 8px; }}
    .brand {{
      font-size: 12px;
      letter-spacing: .12em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 8px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 22px;
      font-weight: 700;
    }}
    .slug {{
      display: inline-block;
      margin: 0 0 16px;
      padding: 4px 10px;
      border-radius: 999px;
      background: rgba(91,140,255,.15);
      color: var(--accent);
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 13px;
    }}
    .phrase {{
      margin: 0 0 20px;
      font-size: 16px;
      line-height: 1.5;
      color: var(--text);
    }}
    form {{ text-align: left; }}
    label {{
      display: block;
      font-size: 13px;
      color: var(--muted);
      margin-bottom: 6px;
    }}
    input[type="password"] {{
      width: 100%;
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid rgba(255,255,255,.18);
      background: rgba(0,0,0,.15);
      color: var(--text);
      font-size: 16px;
      outline: none;
      transition: border-color .15s ease, box-shadow .15s ease;
    }}
    @media (prefers-color-scheme: light) {{
      input[type="password"] {{ background: #fff; border-color: #c8d4ef; }}
    }}
    input[type="password"]:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(91,140,255,.25);
    }}
    button {{
      width: 100%;
      margin-top: 14px;
      padding: 12px 18px;
      border: 0;
      border-radius: 14px;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      color: #fff;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 8px 24px rgba(91,140,255,.35);
    }}
    button:hover {{ filter: brightness(1.05); }}
    .error {{
      margin: 0 0 12px;
      padding: 10px 12px;
      border-radius: 12px;
      background: rgba(255,107,138,.12);
      color: var(--error);
      font-size: 14px;
      text-align: center;
    }}
    .footer {{
      margin-top: 18px;
      font-size: 12px;
      color: var(--muted);
      text-align: center;
    }}
  </style>
</head>
<body>
  <main class="card">
    <div class="lock">🔒</div>
    <div class="brand">goSky</div>
    <h1>{safe_title}</h1>
    <div class="slug">/{safe_slug}</div>
    <p class="phrase">{safe_phrase}</p>
    <form method="post" action="{safe_action}">
      {hidden_html}{error_block}
      <label for="password">Пароль</label>
      <input id="password" name="password" type="password" autocomplete="current-password" required autofocus />
      <button type="submit">{submit_label}</button>
    </form>
    <div class="footer">SkyKraft · go.skykraft.su</div>
  </main>
</body>
</html>"""


def build_password_html_response(
    link,
    request,
    *,
    context: PasswordContext,
    form_action: str,
    error: str | None = None,
    hidden_fields: dict[str, str] | None = None,
    status_code: int = 401,
):
    from fastapi.responses import HTMLResponse

    from .config import settings

    cookie_name = password_phrase_cookie_name(link.slug, context)
    try:
        phrase_index = int(request.cookies.get(cookie_name, "0"))
    except ValueError:
        phrase_index = 0
    phrase, next_index = pick_password_phrase(context, phrase_index)
    html = render_password_page(
        slug=link.slug,
        title=link.title,
        phrase=phrase,
        form_action=form_action,
        context=context,
        error=error,
        hidden_fields=hidden_fields,
    )
    response = HTMLResponse(content=html, status_code=status_code)
    response.set_cookie(
        key=cookie_name,
        value=str(next_index),
        max_age=365 * 24 * 3600,
        path="/",
        samesite="lax",
        httponly=True,
        secure=settings.cookie_secure,
    )
    return response
