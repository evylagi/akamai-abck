# ABCK Token Generator

Beautiful React dashboard for token generation with Flask API and Python automation.

## Setup

```bash
pip install -r requirements.txt
npm install
npm run build
python server.py
```

Open **http://localhost:5050**

## Features

- 🎨 Real-time stats dashboard
- ⚡ REST API endpoints
- 🔒 Akamai bypass
- ♾️ Unlimited tokens
- 💻 Beautiful UI

## API

```
GET /api/stats              - Statistics
POST /api/start             - Start generation
POST /api/stop              - Stop generation
GET /api/tokens             - Get tokens
POST /api/save-token        - Save token
GET /api/export?format=txt  - Export tokens
```

## Env Variables

```
TOKEN_SERVER_HOST=0.0.0.0
TOKEN_SERVER_PORT=5050
CHROME_BINARY=/path/to/chrome
```

## Deploy to Railway

```bash
git push railway main
```

Uses `Procfile` for process management.
