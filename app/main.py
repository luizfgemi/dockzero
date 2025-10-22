from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
import docker
import time
import os

app = FastAPI()
client = docker.from_env()

WSL_DISTRO = os.getenv("DASHBOARD_WSL_DISTRO", "Ubuntu")  # usado na página /exec/{name}

# ---------- helpers ----------

def first_mapped_port(container) -> str | None:
    ports = (container.attrs.get("NetworkSettings", {}) or {}).get("Ports", {}) or {}
    for port, mappings in ports.items():
        if mappings:
            return mappings[0].get("HostPort")
    return None

def calc_cpu_percent(stats: dict) -> float | None:
    try:
        cpu_stats = stats.get("cpu_stats", {})
        precpu = stats.get("precpu_stats", {})
        cpu_total = cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
        pre_total = precpu.get("cpu_usage", {}).get("total_usage", 0)
        sys_total = cpu_stats.get("system_cpu_usage", 0)
        pre_sys = precpu.get("system_cpu_usage", 0)
        online_cpus = cpu_stats.get("online_cpus") or (cpu_stats.get("cpu_usage", {}).get("percpu_usage") and len(cpu_stats["cpu_usage"]["percpu_usage"])) or 1

        cpu_delta = cpu_total - pre_total
        sys_delta = sys_total - pre_sys
        if cpu_delta > 0 and sys_delta > 0 and online_cpus:
            return (cpu_delta / sys_delta) * online_cpus * 100.0
    except Exception:
        pass
    return None

def calc_mem_mb(stats: dict) -> float | None:
    try:
        mem_stats = stats.get("memory_stats", {}) or {}
        usage = float(mem_stats.get("usage", 0.0))
        return usage / (1024 * 1024)
    except Exception:
        return None

# ---------- UI (dashboard) ----------

@app.get("/", response_class=HTMLResponse)
def dashboard(_: Request):
    html = """
    <html>
    <head>
      <title>Docker Dashboard</title>
      <meta charset="utf-8"/>
      <meta name="viewport" content="width=device-width, initial-scale=1"/>
      <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='0.9em' font-size='90'>🧩</text></svg>">
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
    return HTMLResponse(content=html)

# ---------- API (dados do dashboard) ----------

@app.get("/containers", response_class=JSONResponse)
def list_containers(_: Request):
    """
    Retorna lista de containers com:
    - name, status
    - link (http://localhost:<port>)
    - cpu (%), mem_mb
    """
    result = []
    containers = client.containers.list(all=True)
    for c in containers:
        host_port = first_mapped_port(c)
        link = f"http://localhost:{host_port}" if host_port else None

        cpu = None
        mem = None
        try:
            stats = c.stats(stream=False)
            cpu = calc_cpu_percent(stats)
            mem = calc_mem_mb(stats)
        except Exception:
            pass

        result.append({
            "name": c.name,
            "status": c.status,
            "link": link,
            "cpu": round(cpu, 1) if cpu is not None else None,
            "mem_mb": round(mem, 0) if mem is not None else None,
        })
    return JSONResponse(result)

@app.post("/action/{name}/{op}", response_class=JSONResponse)
def action(name: str, op: str):
    """
    Executa ação no container: start | stop | restart
    (o painel atualiza via cron de 10s)
    """
    c = client.containers.get(name)
    if op == "restart":
        c.restart()
    elif op == "stop":
        c.stop()
    elif op == "start":
        c.start()
    else:
        return JSONResponse({"ok": False, "error": "operação inválida"}, status_code=400)
    time.sleep(0.1)
    return JSONResponse({"ok": True})

# ---------- Logs (UI + raw) ----------

@app.get("/logs/{name}", response_class=HTMLResponse)
def container_logs(name: str, tail: int = Query(default=200, ge=1, le=5000)):
    """
    Página de logs com auto-refresh (5s) e auto-scroll.
    Use ?tail=N para ajustar o tail.
    """
    # usar uma rota separada para o conteúdo em texto -> /logs_raw/{name}
    html = f"""
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
    return HTMLResponse(content=html)

@app.get("/logs_raw/{name}", response_class=PlainTextResponse)
def container_logs_raw(name: str, tail: int = Query(default=200, ge=1, le=5000)):
    """
    Conteúdo textual dos logs (tail N), usado pela página /logs/{name}.
    """
    c = client.containers.get(name)
    try:
        logs = c.logs(tail=tail).decode("utf-8", errors="ignore")
    except Exception as e:
        logs = f"[erro] {e}"
    return PlainTextResponse(logs)

# ---------- Exec (Windows Terminal helper) ----------

@app.get("/exec/{name}", response_class=HTMLResponse)
def open_in_terminal(name: str):
    """
    Exibe o comando pronto para abrir o container no Windows Terminal.
    Usa WSL (distro configurável via env DASHBOARD_WSL_DISTRO).
    """
    # usa bash por padrão; se quiser sh ou zsh, mude aqui
    cmd = f"wsl -d {WSL_DISTRO} docker exec -it {name} bash"
    html = f"""
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
      <pre id="cmd">{cmd}</pre>
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
    return HTMLResponse(content=html)
