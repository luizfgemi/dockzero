# Docker Dashboard

Aplicação FastAPI para inspecionar containers Docker locais, visualizar métricas simples e acionar start, stop e restart pelo navegador.

## Execução

```bash
docker-compose up
```

A interface fica disponível em `http://localhost:8000`. Se preferir rodar sem Docker, instale as dependências de `app/requirements.txt` e inicie com `uvicorn main:app --host 0.0.0.0 --port 8000` dentro da pasta `app`.
