"""HTML rendering helpers for the dashboard page."""
from __future__ import annotations

import json
from html import escape
from textwrap import dedent
from typing import Any, Mapping

from app.views.assets import FAVICON_DATA_URI


def render_dashboard(auto_refresh_seconds: int, title: str, messages: Mapping[str, Any]) -> str:
    """Return the HTML contents for the dashboard page."""
    refresh_ms = auto_refresh_seconds * 1000
    safe_title = escape(title)
    dashboard_messages = messages["dashboard"]
    footer_hint = escape(dashboard_messages["auto_refresh"].format(seconds=auto_refresh_seconds))
    loading_text = escape(dashboard_messages["loading"])
    messages_json = json.dumps(messages, ensure_ascii=False)
    return dedent(
        f"""
        <html>
        <head>
          <title>{safe_title}</title>
          <meta charset="utf-8"/>
          <meta name="viewport" content="width=device-width, initial-scale=1"/>
          <link rel="icon" href="{FAVICON_DATA_URI}">
          <style>
            :root {{ --bg:#0d1117; --fg:#c9d1d9; --muted:#777; --line:#222; --ok:#2ecc71; --bad:#e74c3c; --link:#58a6ff; }}
            * {{ box-sizing: border-box; }}
            body {{ margin:0; font-family: Arial, sans-serif; background: var(--bg); color: var(--fg); }}
            header {{ text-align:center; padding:22px 12px; font-size:26px; }}
            .container {{ max-width: 820px; margin: 0 auto; padding: 0 12px 40px; }}
            a {{ color: var(--link); text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            .card {{ padding: 12px 16px; border-bottom: 1px solid var(--line);
                    display:flex; align-items:center; gap:16px; }}
            .name {{ font-weight: 600; }}
            .grow {{ flex: 1 1 auto; min-width: 180px; }}
            .meta {{ font-size: 12px; color: var(--muted); margin-top:4px; }}
            .status {{ font-weight: bold; font-size: 14px; min-width: 26px; text-align:center; }}
            .running {{ color: var(--ok); }}
            .stopped {{ color: var(--bad); }}
            .actions {{ display:flex; gap:8px; }}
            .btn {{ border:1px solid var(--line); background:#11161d; color:var(--fg); padding:6px 8px; border-radius:8px; cursor:pointer; font-size:13px; }}
            .btn:hover {{ filter: brightness(1.1); }}
            .btn:disabled {{ opacity: .5; cursor: not-allowed; }}
            .footer {{ text-align:center; margin-top:12px; font-size:12px; color:var(--muted); }}

            #toast {{
              position: fixed; right: 18px; bottom: 18px; background:#11161d; color:var(--fg);
              padding:10px 12px; border:1px solid var(--line); border-radius:10px; opacity:0;
              transform: translateY(10px); transition: opacity .2s ease, transform .2s ease;
              pointer-events:none; box-shadow: 0 8px 24px rgba(0,0,0,.35);
              max-width: 60vw; font-size: 14px;
            }}
            #toast.show {{ opacity:1; transform: translateY(0); }}

            .row {{ display:flex; align-items:center; gap:12px; width:100%; flex-wrap:wrap; }}
            .link {{ min-width: 240px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}

            .mini {{ display:flex; gap:6px; }}
          </style>
        </head>
        <body>
          <header>🧩 {safe_title}</header>
          <div id="content" class="container">{loading_text}</div>
          <div class="footer">{footer_hint}</div>
          <div id="toast"></div>

          <script>
            const I18N = {messages_json};
            const DASH = I18N.dashboard;

            function format(msg, vars) {{
              return msg.replace(/\\{{(\\w+)\\}}/g, (_, key) => {{
                if (!vars || vars[key] === undefined) return '{' + key + '}';
                return String(vars[key]);
              }});
            }}

            function toast(msg) {{
              const t = document.getElementById('toast');
              t.textContent = msg;
              t.classList.add('show');
              clearTimeout(window.__toastTimer);
              window.__toastTimer = setTimeout(()=> t.classList.remove('show'), 2000);
            }}

            async function api(url, opts) {{
              const res = await fetch(url, opts);
              if (!res.ok) throw new Error(await res.text());
              return res.json ? res.json() : res.text();
            }}

            async function doAction(name, action) {{
              try {{
                await api(`/action/${{encodeURIComponent(name)}}/${{action}}`, {{method:'POST'}});
                toast(format(DASH.toast_action_success, {{name, action}}));
              }} catch (e) {{
                toast(format(DASH.toast_action_error, {{name, action}}));
              }}
            }}

            function fmt(v, digits=1) {{
              return (v === null || v === undefined) ? '-' : Number(v).toFixed(digits);
            }}

            function linkHtmlFor(c) {{
              if (!c.link) return `<span class="link" style="color:#888"><em>${{DASH.no_ports}}</em></span>`;
              const logs = `/logs/${{encodeURIComponent(c.name)}}`;
              const term = `/exec/${{encodeURIComponent(c.name)}}`;
              return `
                <a class="link" href="${{c.link}}" target="_blank">${{c.link}}</a>
                <span class="mini">
                  <a class="btn" href="${{logs}}" target="_blank" title="${{DASH.button_logs}}">📜</a>
                  <a class="btn" href="${{term}}" target="_blank" title="${{DASH.button_terminal}}">💻</a>
                </span>
              `;
            }}

            function updateMetrics(metrics) {{
              Object.keys(metrics).forEach(name => {{
                const encoded = encodeURIComponent(name);
                const card = document.querySelector(`.card[data-container=\"${{encoded}}\"]`);
                if (!card) return;
                const meta = card.querySelector('.meta');
                if (!meta) return;
                const entry = metrics[name] || {{}};
                const cpu = fmt(entry.cpu, 1);
                const mem = fmt(entry.mem_mb, 0);
                meta.innerHTML = format(DASH.metrics, {{cpu, mem}});
              }});
            }}

            async function fetchMetrics(names) {{
              if (!names.length) return;
              const query = names.map(n => `names=${{encodeURIComponent(n)}}`).join('&');
              try {{
                const metrics = await api(`/containers/metrics?${{query}}`);
                updateMetrics(metrics);
              }} catch (e) {{
                console.warn('Failed to load metrics', e);
              }}
            }}

            function renderCard(container) {{
              const statusCls = container.status === 'running' ? 'running' : 'stopped';
              const statusIcon = container.status === 'running' ? DASH.status_running : DASH.status_stopped;
              const linkHtml = linkHtmlFor(container);
              const cpu = fmt(container.cpu, 1);
              const mem = fmt(container.mem_mb, 0);
              const metrics = format(DASH.metrics, {{cpu, mem}});
              const encoded = encodeURIComponent(container.name);

              return `
                <div class="card" data-container="${{encoded}}">
                  <div class="status ${{statusCls}}">${{statusIcon}}</div>
                  <div class="grow">
                    <div class="name">${{container.name}}</div>
                    <div class="meta">${{metrics}}</div>
                  </div>
                  <div class="grow row">
                    ${{linkHtml}}
                  </div>
                  <div class="actions">
                    <button class="btn" title="${{DASH.button_restart}}" onclick="doAction('${{container.name}}','restart')">🔄</button>
                    <button class="btn" title="${{DASH.button_stop}}" ${{container.status==='running'?'':'disabled'}} onclick="doAction('${{container.name}}','stop')">⏹</button>
                    <button class="btn" title="${{DASH.button_start}}" ${{container.status!=='running'?'':'disabled'}} onclick="doAction('${{container.name}}','start')">▶️</button>
                  </div>
                </div>
              `;
            }}

            function applyUpdate(containers) {{
              const div = document.getElementById('content');
              const existingCards = new Map([...div.querySelectorAll('.card')].map(card => [decodeURIComponent(card.dataset.container || ''), card]));

              containers.forEach(container => {{
                const name = container.name;
                const encoded = encodeURIComponent(name);
                let card = existingCards.get(name);

                if (!card) {{
                  const temp = document.createElement('div');
                  temp.innerHTML = renderCard(container);
                  card = temp.firstElementChild;
                  div.appendChild(card);
                }} else {{
                  existingCards.delete(name);
                  const statusCls = container.status === 'running' ? 'running' : 'stopped';
                  const statusIcon = container.status === 'running' ? DASH.status_running : DASH.status_stopped;
                  card.querySelector('.status').innerHTML = statusIcon;
                  card.querySelector('.status').className = `status ${{statusCls}}`;
                  const nameEl = card.querySelector('.name');
                  if (nameEl) nameEl.textContent = name;

                  const linkWrap = card.querySelector('.grow.row');
                  if (linkWrap) linkWrap.innerHTML = linkHtmlFor(container);

                  const meta = card.querySelector('.meta');
                  if (meta && (container.cpu != null || container.mem_mb != null)) {{
                    const cpu = fmt(container.cpu, 1);
                    const mem = fmt(container.mem_mb, 0);
                    meta.innerHTML = format(DASH.metrics, {{cpu, mem}});
                  }}

                  const [restartBtn, stopBtn, startBtn] = card.querySelectorAll('.actions .btn');
                  if (restartBtn) restartBtn.setAttribute('onclick', `doAction('${{name}}','restart')`);
                  if (stopBtn) {{
                    stopBtn.toggleAttribute('disabled', container.status !== 'running');
                    stopBtn.setAttribute('onclick', `doAction('${{name}}','stop')`);
                  }}
                  if (startBtn) {{
                    startBtn.toggleAttribute('disabled', container.status === 'running');
                    startBtn.setAttribute('onclick', `doAction('${{name}}','start')`);
                  }}
                }}
              }});

              existingCards.forEach(card => {{
                card.remove();
              }});
            }}

            async function loadContainers() {{
              try {{
                const data = await api('/containers?include_metrics=0');
                const div = document.getElementById('content');
                if (!data.length) {{
                  div.innerHTML = `<p style="text-align:center;">${{DASH.no_containers}}</p>`;
                  return;
                }}
                if (!div.dataset.initialized) {{
                  div.innerHTML = data.map(renderCard).join('');
                  div.dataset.initialized = '1';
                }} else {{
                  applyUpdate(data);
                }}
                const names = data.map(c => c.name);
                fetchMetrics(names);
              }} catch (e) {{
                toast(DASH.toast_load_error);
              }}
            }}

            loadContainers();
            setInterval(() => {{
              loadContainers().catch(() => {{ /* handled in loadContainers */ }});
            }}, {refresh_ms});
          </script>
        </body>
        </html>
        """
    ).strip()
