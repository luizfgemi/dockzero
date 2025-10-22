"""HTML rendering helpers for the exec/terminal page."""
from __future__ import annotations

from textwrap import dedent


def render_terminal_page(name: str, command: str) -> str:
    """Return the HTML contents that show the exec command."""
    return dedent(
        f"""
        <html>
        <head>
          <meta charset="utf-8"/>
          <title>Terminal - {name}</title>
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
          <h3>💻 Abrir container no Windows Terminal</h3>
          <p>Copie e cole este comando no PowerShell/Windows Terminal:</p>
          <pre id="cmd">{command}</pre>
          <button onclick="copyCmd()">📋 Copiar comando</button>
          &nbsp;&nbsp; <a href="/" target="_blank">voltar ao dashboard</a>
          <div id="toast">Copiado!</div>
          <script>
            function copyCmd() {{
              const text = document.getElementById('cmd').textContent;
              navigator.clipboard.writeText(text);
              const toast = document.getElementById('toast');
              toast.classList.add('show');
              setTimeout(()=>toast.classList.remove('show'),1500);
            }}
          </script>
        </body>
        </html>
        """
    ).strip()
