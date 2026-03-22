# NEURON-X Omega — Deployment Guide

## Prerequisites

- Python 3.10+
- Node.js 18+ (for web dashboard)

## 1. Install Core Engine

```bash
cd packages/neuronx-core
pip install -e .
```

Verify:
```bash
python -c "from neuronx import NeuronBrain; print('OK')"
```

## 2. Run Tests

```bash
cd packages/neuronx-core
python -m pytest tests/ -v
```

Expected: `91 passed`

## 3. Start API Server

```bash
pip install fastapi uvicorn
cd packages/neuronx-server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Server runs at `http://localhost:8000`. Docs at `/docs`.

## 4. Start Web Dashboard

```bash
cd packages/neuronx-web
npm install
npm run dev
```

Dashboard runs at `http://localhost:5173`.

## 5. Build TypeScript SDK

```bash
cd packages/neuronx-sdk-js
npm install
npm run build
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEURONX_DATA_DIR` | `data` | Directory for .soma files |
| `NEURONX_BRAIN_NAME` | `default` | Brain name |

## Docker (Optional)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY packages/neuronx-core /app/packages/neuronx-core
COPY packages/neuronx-server /app/packages/neuronx-server
RUN pip install -e packages/neuronx-core[server]
EXPOSE 8000
CMD ["uvicorn", "packages.neuronx-server.app.main:app", "--host", "0.0.0.0"]
```

## Production Checklist

- [ ] Set `NEURONX_DATA_DIR` to persistent volume
- [ ] Configure rate limiting in `config.py`
- [ ] Enable HTTPS via reverse proxy (nginx/caddy)
- [ ] Set up backup cron for `.soma` files
- [ ] Monitor `.nrnlog` files for audit history
