"""HTML rendering helpers for the dashboard page."""
from __future__ import annotations

DASHBOARD_HTML = """
<html>
<head>
  <title>Docker Dashboard</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='0.9em' font-size='90'>🧩</text></svg>'">
  <style>
    :root { --bg:#0d1117; --fg:#c9d1d9; --muted:#777; --line:#222; --ok:#2ecc71; --bad:#e74c3c; --link:#58a6ff; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: Arial, sans-serif; background: var(--bg); color: var(--fg); }
    header { text-align:center; padding:22px 12px; font-size:26px; }
    .container { max-width: 820px; margin: 0 auto; padding: 0 12px 40px; }
    a { color: var(--link); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .card { padding: 12px 16px; border-bottom: 1px solid var(--line);
            display:flex; align-items:center; gap:16px; }
    .name { font-weight: 600; }
    .grow { flex: 1 1 auto; min-width: 180px; }
    .meta { font-size: 12px; color: var(--muted); margin-top:4px; }
    .status { font-weight: bold; font-size: 14px; min-width: 26px; text-align:center; }
    .running { color: var(--ok); }
    .stopped { color: var(--bad); }
    .actions { display:flex; gap:8px; }
    .btn { border:1px solid var(--line); background:#11161d; color:var(--fg); padding:6px 8px; border-radius:8px; cursor:pointer; font-size:13px; }
    .btn:hover { filter: brightness(1.1); }
    .btn:disabled { opacity: .5; cursor: not-allowed; }
    .footer { text-align:center; margin-top:12px; font-size:12px; color:var(--muted); }

    #toast {
      position: fixed; right: 18px; bottom: 18px; background:#11161d; color:var(--fg);
      padding:10px 12px; border:1px solid var(--line); border-radius:10px; opacity:0;
      transform: translateY(10px); transition: opacity .2s ease, transform .2s ease;
      pointer-events:none; box-shadow: 0 8px 24px rgba(0,0,0,.35);
      max-width: 60vw; font-size: 14px;
    }
    #toast.show { opacity:1; transform: translateY(0); }

    .row { display:flex; align-items:center; gap:12px; width:100%; flex-wrap:wrap; }
    .link { min-width: 240px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

    .mini { display:flex; gap:6px; }
  </style>
</head>
<body>
  <header>🧩 Docker Dashboard</header>
  <div id="content" class="container">Carregando containers...</div>
  <div class="footer">Atualiza automaticamente a cada 10 s</div>
  <div id="toast"></div>

  <script>
    function toast(msg) {
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.classList.add('show');
      clearTimeout(window.__toastTimer);
      window.__toastTimer = setTimeout(()=> t.classList.remove('show'), 2000);
    }

    async function api(url, opts) {
      const res = await fetch(url, opts);
      if (!res.ok) throw new Error(await res.text());
      return res.json ? res.json() : res.text();
    }

    async function doAction(name, action) {
      try {
        await api(`/action/${encodeURIComponent(name)}/${action}`, {method:'POST'});
        toast(`✅ ${name}: ${action} enviado`);
      } catch (e) {
        toast(`❌ ${name}: falha em ${action}`);
      }
    }

    function fmt(v, digits=1) {
      return (v === null || v === undefined) ? '-' : Number(v).toFixed(digits);
    }

    function linkHtmlFor(c) {
      if (!c.link) return '<span class="link" style="color:#888"><em>sem portas expostas</em></span>';
      const logs = `/logs/${encodeURIComponent(c.name)}`;
      const term = `/exec/${encodeURIComponent(c.name)}`;
      return `
        <a class="link" href="${c.link}" target="_blank">${c.link}</a>
        <span class="mini">
          <a class="btn" href="${logs}" target="_blank" title="logs">📜</a>
          <a class="btn" href="${term}" target="_blank" title="terminal">💻</a>
        </span>
      `;
    }

    async function loadContainers() {
      try {
        const data = await api('/containers');
        const div = document.getElementById('content');
        if (!data.length) {
          div.innerHTML = '<p style="text-align:center;">Nenhum container.</p>';
          return;
        }
        div.innerHTML = data.map(c => {
          const statusCls = c.status === 'running' ? 'running' : 'stopped';
          const linkHtml = linkHtmlFor(c);
          const cpu = fmt(c.cpu, 1);
          const mem = fmt(c.mem_mb, 0);

          return `
            <div class="card">
              <div class="status ${statusCls}">${c.status === 'running' ? '🟢' : '🔴'}</div>
              <div class="grow">
                <div class="name">${c.name}</div>
                <div class="meta">CPU: ${cpu}% &nbsp;|&nbsp; Mem: ${mem} MB</div>
              </div>
              <div class="grow row">
                ${linkHtml}
              </div>
              <div class="actions">
                <button class="btn" title="restart" onclick="doAction('${c.name}','restart')">🔄</button>
                <button class="btn" title="stop" ${c.status==='running'?'':'disabled'} onclick="doAction('${c.name}','stop')">⏹</button>
                <button class="btn" title="start" ${c.status!=='running'?'':'disabled'} onclick="doAction('${c.name}','start')">▶️</button>
              </div>
            </div>
          `;
        }).join('');
      } catch (e) {
        toast('Erro ao carregar containers');
      }
    }

    loadContainers();
    setInterval(loadContainers, 10000);
  </script>
</body>
</html>
"""


def render_dashboard() -> str:
    """Return the HTML contents for the dashboard page."""
    return DASHBOARD_HTML
