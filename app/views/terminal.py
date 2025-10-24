"""HTML rendering helpers for the exec/terminal page."""
from __future__ import annotations

import json
from html import escape
from textwrap import dedent
from typing import Any, Iterable, Mapping

from app.views.assets import FAVICON_DATA_URI


def render_terminal_page(
    name: str,
    commands: Iterable[dict[str, str]],
    title: str,
    messages: Mapping[str, Any],
    *,
    base_path: str = "",
) -> str:
    """Return the HTML contents that show the exec command options."""
    safe_title = escape(title)
    safe_name = escape(name)
    terminal_messages = messages["terminal"]
    common_messages = messages["common"]
    instructions = escape(terminal_messages["instructions"])
    copy_button = escape(terminal_messages["copy_button"])
    back_text = escape(common_messages["back_to_dashboard"])
    copied_text = escape(common_messages["copied"])
    toast_message = json.dumps(common_messages["copied"])
    normalized_base = base_path.strip() if base_path else ""
    if normalized_base and not normalized_base.startswith("/"):
        normalized_base = f"/{normalized_base.lstrip('/')}"
    if normalized_base == "/":
        normalized_base = ""

    cards_html: list[str] = []
    for idx, info in enumerate(commands):
        label = escape(info.get("label", f"Command {idx + 1}"))
        command_text = escape(info.get("command", ""))
        cmd_id = f"cmd-{idx}"
        cards_html.append(
            f"""
            <div class=\"cmd-card\">
              <div class=\"cmd-label\">{label}</div>
              <pre id=\"{cmd_id}\">{command_text}</pre>
              <button onclick=\"copyCmd('{cmd_id}')\">{copy_button}</button>
            </div>
            """
        )

    commands_markup = "\n".join(cards_html) or "<p>No command templates configured.</p>"

    return dedent(
        f"""
        <html>
        <head>
          <meta charset=\"utf-8\"/>
          <title>{safe_title} · Exec · {safe_name}</title>
          <link rel=\"icon\" href=\"{FAVICON_DATA_URI}\">
          <style>
            body {{ background:#0d1117; color:#c9d1d9; font-family: monospace; padding:24px; }}
            .cmd-card {{ background:#0f1420; border:1px solid #333; border-radius:10px; padding:16px; margin-bottom:16px; }}
            .cmd-label {{ font-size:14px; margin-bottom:8px; color:#9cb3d3; }}
            pre {{ margin:0; padding:12px; border-radius:8px; background:#0a0f1a; border:1px solid #222; white-space:pre-wrap; word-break:break-word; }}
            button {{ margin-top:10px; background:#11161d; border:1px solid #333; color:#fff; padding:6px 10px;
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
          <div class=\"cmd-list\">
            {commands_markup}
          </div>
          &nbsp;&nbsp; <a href=\"{normalized_base or '/'}\" target=\"_blank\">{back_text}</a>
          <div id=\"toast\">{copied_text}</div>
          <script>
            const TOAST_MSG = {toast_message};

            function copyCmd(id) {{
              const el = document.getElementById(id);
              if (!el) return;
              const text = el.textContent;
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
