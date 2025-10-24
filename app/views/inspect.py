"""HTML rendering helpers for the container inspect page."""
from __future__ import annotations

import json
from html import escape
from textwrap import dedent
from typing import Any, Mapping

from app.views.assets import FAVICON_DATA_URI


def render_inspect_page(
    name: str,
    data: dict[str, Any],
    refresh_seconds: int,
    title: str,
    messages: Mapping[str, Any],
    *,
    base_path: str = "",
) -> str:
    """Return the HTML page that displays detailed container information."""
    refresh_ms = refresh_seconds * 1000
    safe_title = escape(title)
    safe_name = escape(name)
    inspect_messages = messages["inspect"]
    common_messages = messages["common"]

    initial_json = json.dumps(data.get("inspect", {}), indent=2, sort_keys=True, ensure_ascii=False)
    stats_json = json.dumps(data.get("stats", {}), indent=2, sort_keys=True, ensure_ascii=False)
    normalized_base = base_path.strip() if base_path else ""
    if normalized_base and not normalized_base.startswith("/"):
        normalized_base = f"/{normalized_base.lstrip('/')}"
    if normalized_base == "/":
        normalized_base = ""

    return dedent(
        f"""
        <html>
        <head>
          <meta charset="utf-8"/>
          <title>{safe_title} · Inspect · {safe_name}</title>
          <link rel="icon" href="{FAVICON_DATA_URI}">
          <style>
            body {{ background:#0d1117; color:#c9d1d9; font-family: monospace; margin:0; }}
            header {{ padding:16px 20px; border-bottom:1px solid #222; display:flex; justify-content:space-between; align-items:center; gap:12px; }}
            h1 {{ margin:0; font-size:16px; font-weight:600; }}
            .muted {{ color:#888; font-size:12px; }}
            section {{ padding:16px 20px; }}
            pre {{ background:#0f1420; border:1px solid #222; border-radius:12px; padding:16px; overflow:auto; max-height:60vh; }}
            .split {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:16px; }}
            button {{ background:#11161d; border:1px solid #333; color:#c9d1d9; border-radius:8px; padding:6px 10px; cursor:pointer; font-size:12px; }}
            button:hover {{ filter:brightness(1.15); }}
            a {{ color:#58a6ff; text-decoration:none; font-size:12px; }}
            a:hover {{ text-decoration:underline; }}
          </style>
        </head>
        <body>
          <header>
            <div>
              <h1>{safe_title} · Inspect · {safe_name}</h1>
              <div class="muted">{inspect_messages["auto_refresh"].format(seconds=refresh_seconds)}</div>
            </div>
            <div>
              <a href="{normalized_base or '/'}" target="_blank">{common_messages["back_to_dashboard"]}</a>
            </div>
          </header>
          <section class="split">
            <div>
              <div class="muted">{inspect_messages["inspect_heading"]}</div>
              <pre id="inspect">{initial_json}</pre>
            </div>
            <div>
              <div class="muted">{inspect_messages["stats_heading"]}</div>
              <pre id="stats">{stats_json}</pre>
            </div>
          </section>

          <script>
            const REFRESH_MS = {refresh_ms};
            const BASE_PATH = "{normalized_base}";
            const ENDPOINT = `${{BASE_PATH}}/inspect_raw/{escape(name)}`;

            async function loadInspect() {{
              try {{
                const res = await fetch(ENDPOINT);
                if (!res.ok) throw new Error(await res.text());
                const data = await res.json();
                document.getElementById('inspect').textContent = JSON.stringify(data.inspect || {{}}, null, 2);
                document.getElementById('stats').textContent = JSON.stringify(data.stats || {{}}, null, 2);
              }} catch (err) {{
                console.error(err);
              }}
            }}

            setInterval(loadInspect, REFRESH_MS);
          </script>
        </body>
        </html>
        """
    ).strip()


__all__ = ["render_inspect_page"]
