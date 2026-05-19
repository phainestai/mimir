# 🐳 Mimir Docker Quick Start

Two containers make up the Mimir stack:

| Container | Image | Purpose |
|-----------|-------|---------|
| **FOB** (web app) | `411113550285.dkr.ecr.us-east-1.amazonaws.com/mimir:latest` | Django UI + REST API |
| **MCP Facade** | `featurefactory/mimir-mcp:latest` | Connects your AI IDE to FOB |

---

## Option 1: Docker Compose (Recommended)

Runs both containers together — MCP facade waits for FOB to be healthy, then auto-fetches an auth token.

```bash
# Clone and configure
git clone https://github.com/phainestai/mimir.git
cd mimir
cp .env.example .env   # set MIMIR_USER and MIMIR_PASSWORD

# Start the full stack
docker compose up -d

# FOB web UI:  http://localhost:8000
# MCP SSE:     http://localhost:8001/sse
```

---

## Option 2: Run Containers Individually

### Step 1 — Run the FOB (web app)

```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin \
    411113550285.dkr.ecr.us-east-1.amazonaws.com

# Pull and run
docker run -d \
  --name mimir-fob \
  -p 8000:8000 \
  -v $(pwd)/mimir-data:/app/data \
  -e MIMIR_USER=admin \
  -e MIMIR_PASSWORD=changeme \
  -e MIMIR_EMAIL=admin@localhost \
  411113550285.dkr.ecr.us-east-1.amazonaws.com/mimir:latest
```

FOB is ready when `docker logs mimir-fob | grep "Listening"` appears.

### Step 2 — Get your API token

```bash
curl -s -X POST http://localhost:8000/api/auth/token/ \
  -d "username=admin&password=changeme" | python3 -c \
  "import sys,json; print(json.load(sys.stdin)['token'])"
```

Copy the token — you'll need it for the MCP facade and your IDE config.

---

## Connecting Your IDE to the MCP Facade

The MCP facade (`featurefactory/mimir-mcp:latest`) is a public Docker Hub image — no registry login needed.

> **Note:** Older guides referenced `public.ecr.aws/h1b6q4p0/mimir-mcp-facade`; use Docker Hub (`featurefactory/mimir-mcp`) instead.

### Windsurf — `~/.codeium/windsurf/mcp_config.json`

```json
{
  "mcpServers": {
    "mimir": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "MIMIR_SERVER_URL=https://mimir.featurefactory.io",
        "-e", "MIMIR_TOKEN=<your-token>",
        "-e", "MCP_TRANSPORT=stdio",
        "featurefactory/mimir-mcp:latest"
      ]
    }
  }
}
```

### Claude Desktop — `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mimir": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "MIMIR_SERVER_URL=https://mimir.featurefactory.io",
        "-e", "MIMIR_TOKEN=<your-token>",
        "-e", "MCP_TRANSPORT=stdio",
        "featurefactory/mimir-mcp:latest"
      ]
    }
  }
}
```

### Cursor — `~/.cursor/mcp.json`

```json
{
  "mcpServers": {
    "mimir": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "MIMIR_SERVER_URL=https://mimir.featurefactory.io",
        "-e", "MIMIR_TOKEN=<your-token>",
        "-e", "MCP_TRANSPORT=stdio",
        "featurefactory/mimir-mcp:latest"
      ]
    }
  }
}
```

Replace `<your-token>` with your token from Step 2.
For a local FOB, change `MIMIR_SERVER_URL` to `http://localhost:8000`.
Restart your IDE after saving.

---

## Environment Variables

### FOB Container

| Variable | Default | Description |
|----------|---------|-------------|
| `MIMIR_USER` | `admin` | Default superuser username |
| `MIMIR_PASSWORD` | `changeme` | Default superuser password ⚠️ Change this! |
| `MIMIR_EMAIL` | `admin@localhost` | Default superuser email |
| `MIMIR_DB_PATH` | `/app/data/mimir.db` | SQLite database path |
| `DJANGO_DEBUG` | `False` | Django debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed hosts |

### MCP Facade Container

| Variable | Default | Description |
|----------|---------|-------------|
| `MIMIR_SERVER_URL` | `http://web:8000` | FOB URL (local or hosted) |
| `MIMIR_TOKEN` | — | FOB auth token |
| `MIMIR_USER` | `admin` | Used to auto-fetch token if MIMIR_TOKEN is blank |
| `MIMIR_PASSWORD` | `changeme` | Used to auto-fetch token if MIMIR_TOKEN is blank |
| `MCP_TRANSPORT` | `sse` | `stdio` for IDE, `sse` for server |
| `MCP_PORT` | `8001` | Port for SSE transport |

---

## Container Management

```bash
# View logs
docker logs -f mimir-fob

# Stop
docker stop mimir-fob

# Update to latest
docker stop mimir-fob && docker rm mimir-fob
docker pull 411113550285.dkr.ecr.us-east-1.amazonaws.com/mimir:latest
docker pull featurefactory/mimir-mcp:latest
# re-run with same docker run command above for FOB; IDE/container uses latest MCP image on next `docker run`
```

## Troubleshooting

### FOB won't start
```bash
docker logs mimir-fob
lsof -i :8000   # check port conflict
```

### MCP facade can't reach FOB
```bash
# Verify FOB is healthy
curl -s http://localhost:8000/health/

# Test token fetch manually
curl -s -X POST http://localhost:8000/api/auth/token/ \
  -d "username=admin&password=changeme"
```

### Database issues
```bash
# Backup
cp mimir-data/mimir.db mimir-data/mimir.db.backup

# Start fresh (WARNING: deletes all data)
rm -rf mimir-data/ && mkdir mimir-data
docker restart mimir-fob
```
