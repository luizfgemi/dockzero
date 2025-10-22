"""HTML rendering helpers for the exec/terminal page."""
from __future__ import annotations

import json
from html import escape
from textwrap import dedent
from typing import Any, Mapping

from app.views.assets import FAVICON_DATA_URI


def render_terminal_page(name: str, command: str, title: str, messages: Mapping[str, Any]) -> str:
    """Return the HTML contents that show the exec command."""
    safe_title = escape(title)
    safe_name = escape(name)
    terminal_messages = messages["terminal"]
    common_messages = messages["common"]
    instructions = escape(terminal_messages["instructions"])
    copy_button = escape(terminal_messages["copy_button"])
    back_text = escape(common_messages["back_to_dashboard"])
    copied_text = escape(common_messages["copied"])
    toast_message = json.dumps(common_messages["copied"])
    return dedent(
        f"""
        <html>
        <head>
          <meta charset="utf-8"/>
          <title>{safe_title} · Exec · {safe_name}</title>
          <link rel="icon" href="{FAVICON_DATA_URI}">
          <style>
            body {{ background:#0d1117; color:#c9d1d9; font-family: monospace; padding:24px; }}
            pre {{ background:#0f1420; padding:12px; border:1px solid #333; border-radius:8px; }}
            button {{ background:#11161d; border:1px solid #333; color:#fff; padding:6px 10px;
                     border-radius:8px; cursor:pointer; }}
            button:hover {{ filter: brightness(1.2); }}
            a {{ color:#58a6ff; text-decoration:none; }}
            a:hover {{ text-decoration:underline; }}
            #toast {{ position:fixed; bottom:20px; right:20px; background:#11161d; padding:10px 14px;
                     border-radius:8px; border:1px solid #333; opacity:0; transition:.3s; }}
            #toast.show {{ opacity:1; }}
          </style>
        </head>
        <body>
          <h3>💻 {safe_title} · Exec · {safe_name}</h3>
          <p>{instructions}</p>
          <pre id="cmd">{command}</pre>
          <button onclick="copyCmd()">{copy_button}</button>
          &nbsp;&nbsp; <a href="/" target="_blank">{back_text}</a>
          <div id="toast">{copied_text}</div>
          <script>
            const TOAST_MSG = {toast_message};

            function copyCmd() {{
              const text = document.getElementById('cmd').textContent;
              navigator.clipboard.writeText(text);
              const toast = document.getElementById('toast');
              toast.textContent = TOAST_MSG;
              toast.classList.add('show');
              setTimeout(()=>toast.classList.remove('show'),1500);
            }}
          </script>
        </body>
        </html>
        """
    ).strip()
