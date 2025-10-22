"""HTML rendering helpers for the logs pages."""
from __future__ import annotations

import json
from html import escape
from textwrap import dedent
from typing import Any, Mapping

from app.views.assets import FAVICON_DATA_URI


def render_logs_page(
    name: str,
    tail: int,
    refresh_seconds: int,
    max_tail: int,
    title: str,
    messages: Mapping[str, Any],
) -> str:
    """Return the HTML page used to display container logs."""
    refresh_ms = refresh_seconds * 1000
    safe_title = escape(title)
    safe_name = escape(name)
    logs_messages = messages["logs"]
    common_messages = messages["common"]
    refresh_label = escape(logs_messages["refresh_hint"].format(seconds=refresh_seconds))
    tail_label = escape(logs_messages["tail_label"])
    apply_button = escape(logs_messages["apply_button"])
    loading_text = escape(logs_messages["loading"])
    back_text = escape(common_messages["back_to_dashboard"])
    copied_text = escape(common_messages["copied"])
    toast_tail_applied = json.dumps(logs_messages["toast_tail_applied"])
    toast_default = json.dumps(common_messages["copied"])
    return dedent(
        f"""
        <html>
        <head>
          <meta charset="utf-8"/>
          <title>{safe_title} · Logs · {safe_name}</title>
          <link rel="icon" href="{FAVICON_DATA_URI}">
          <style>
            body {{ background:#0d1117; color:#c9d1d9; font-family: monospace; margin:0; }}
            header {{ padding:12px 16px; border-bottom:1px solid #222; }}
            .muted {{ color:#888; font-size:12px; }}
            pre {{ margin:0; padding:12px 16px; white-space:pre-wrap; }}
            .bar {{ display:flex; gap:12px; align-items:center; }}
            a {{ color:#58a6ff; text-decoration:none; }}
            a:hover {{ text-decoration:underline; }}
            input[type=number] {{ width:90px; background:#0f1420; color:#c9d1d9; border:1px solid #333; border-radius:8px; padding:4px 6px; }}
            button {{ background:#11161d; color:#fff; border:1px solid #333; border-radius:8px; padding:6px 8px; cursor:pointer; }}
            button:hover {{ filter:brightness(1.1); }}
            #toast {{ position:fixed; right:18px; bottom:18px; background:#11161d; color:#c9d1d9;
                     padding:10px 12px; border:1px solid #333; border-radius:10px; opacity:0;
                     transform: translateY(10px); transition:.2s; pointer-events:none; }}
            #toast.show {{ opacity:1; transform: translateY(0); }}
          </style>
        </head>
        <body>
          <header>
            <div class="bar">
              <strong>🧩 {safe_title} · Logs: {safe_name}</strong>
              <span class="muted">{refresh_label}</span>
              <form id="tailForm" onsubmit="return false" class="bar">
                <label>{tail_label}</label>
                <input id="tail" type="number" min="1" max="{max_tail}" value="{tail}"/>
                <button onclick="applyTail()">{apply_button}</button>
              </form>
              <a href="/" target="_blank">{back_text}</a>
            </div>
          </header>
          <pre id="logbox">{loading_text}</pre>
          <div id="toast">{copied_text}</div>

          <script>
            const name_ = {name!r};
            const TOAST_TAIL_APPLIED = {toast_tail_applied};
            const TOAST_DEFAULT = {toast_default};

            function toast(msg) {{
              const t = document.getElementById('toast');
              t.textContent = msg || TOAST_DEFAULT;
              t.classList.add('show');
              clearTimeout(window.__toastTimer);
              window.__toastTimer = setTimeout(()=> t.classList.remove('show'), 1500);
            }}

            async function loadLogs() {{
              const tail = document.getElementById('tail').value || {tail};
              const res = await fetch(`/logs_raw/${{encodeURIComponent(name_)}}?tail=${{tail}}`);
              const txt = await res.text();
              const box = document.getElementById('logbox');
              const atBottom = (window.innerHeight + window.scrollY) >= (document.body.offsetHeight - 4);
              box.textContent = txt;
              if (atBottom) window.scrollTo({{top: document.body.scrollHeight}});
            }}

            function applyTail() {{
              loadLogs();
              toast(TOAST_TAIL_APPLIED);
            }}

            loadLogs();
            setInterval(loadLogs, {refresh_ms});
          </script>
        </body>
        </html>
        """
    ).strip()
