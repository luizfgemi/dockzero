"""HTML rendering helpers for the logs pages."""
from __future__ import annotations

from textwrap import dedent


def render_logs_page(name: str, tail: int) -> str:
    """Return the HTML page used to display container logs."""
    return dedent(
        f"""
        <html>
        <head>
          <meta charset="utf-8"/>
          <title>Logs - {name}</title>
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
              <strong>🧩 Logs: {name}</strong>
              <span class="muted">auto-refresh 5s</span>
              <form id="tailForm" onsubmit="return false" class="bar">
                <label>tail</label>
                <input id="tail" type="number" min="1" max="5000" value="{tail}"/>
                <button onclick="applyTail()">aplicar</button>
              </form>
              <a href="/" target="_blank">voltar ao dashboard</a>
            </div>
          </header>
          <pre id="logbox">carregando...</pre>
          <div id="toast">Copiado!</div>

          <script>
            const name_ = {name!r};
            function toast(msg) {{
              const t = document.getElementById('toast');
              t.textContent = msg || 'OK';
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
              toast('Tail aplicado');
            }}

            loadLogs();
            setInterval(loadLogs, 5000);
          </script>
        </body>
        </html>
        """
    ).strip()
