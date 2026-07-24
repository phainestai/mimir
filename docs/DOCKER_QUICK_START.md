# 🐳 Mimir Docker Quick Start

Two containers make up the Mimir stack:

| Container | Image | Purpose |
|-----------|-------|---------|
| **FOB** (web app) | built from source (`docker build`) | Django UI + REST API |
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
# Build from source (one-time)
git clone https://github.com/phainestai/mimir.git
cd mimir
docker build -t mimir-web:local .

# Run
# Optional: add -e GITHUB_TOKEN=... -e GITHUB_BUG_REPO=phainestai/mimir for Feedback → GitHub Issues
docker run -d \
  --name mimir-fob \
  -p 8000:8000 \
  -v $(pwd)/mimir-data:/app/data \
  -e MIMIR_USER=admin \
  -e MIMIR_PASSWORD=changeme \
  -e MIMIR_EMAIL=admin@localhost \
  mimir-web:local
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
        "-e", "MIMIR_DEV_ROOT=/Users/you/GitHub",
        "-v", "/Users/you/GitHub:/Users/you/GitHub",
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
        "-e", "MIMIR_DEV_ROOT=/Users/you/GitHub",
        "-v", "/Users/you/GitHub:/Users/you/GitHub",
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
        "-e", "MIMIR_DEV_ROOT=/Users/you/GitHub",
        "-v", "/Users/you/GitHub:/Users/you/GitHub",
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
Replace `/Users/you/GitHub` with the folder where your repositories live (use the same path in `MIMIR_DEV_ROOT` and the `-v` mount).
For a local FOB, change `MIMIR_SERVER_URL` to `http://localhost:8000` (or `http://host.docker.internal:8000` from Docker Desktop on macOS/Windows).
Restart your IDE after saving.

---

## Filesystem tools (export / import)

Most MCP tools (list, get, create, update) talk to the hosted API only — **no volume mount required**.

These tools read or write markdown on **your machine**:

| Tool | Needs mount |
|------|-------------|
| `export_workflow_to_local` | Yes |
| `import_workflow_from_local` | Yes (plus local FOB or `mimir-local`; see below) |
| `apply_upload_protocol` | Yes (plus local FOB or `mimir-local`) |
| `create_pip_from_protocol` | Yes (plus local FOB or `mimir-local`) |

The Docker facade runs inside an isolated container. Without a bind mount, export would write to ephemeral container storage and disappear when the container exits.

**Required setup:**

1. Set `MIMIR_DEV_ROOT` to your development folder (parent of your repos).
2. Bind-mount the same folder: `-v "<host-path>:<host-path>"`.
3. Use paths under that root (absolute or relative — relative paths resolve against `MIMIR_DEV_ROOT`).

**Examples:**

| OS | `MIMIR_DEV_ROOT` | Volume mount |
|----|------------------|--------------|
| macOS / Linux | `/Users/you/GitHub` | `-v /Users/you/GitHub:/Users/you/GitHub` |
| Windows (Docker Desktop) | `C:/Users/you/GitHub` | `-v C:/Users/you/GitHub:C:/Users/you/GitHub` |

> **Note:** `$HOME`, `$PWD`, and `%USERPROFILE%` are **not** expanded in IDE MCP JSON — use explicit paths.

**Alternative:** run `manage.py mcp_server` (`mimir-local`) for filesystem tools without Docker mounts. CRUD against hosted FOB can still use the Docker facade.

**Import against hosted FOB:** the server cannot read files on your laptop. Use `mimir-local`, or point Docker MCP at a local FOB (`http://host.docker.internal:8000`) with the volume mount above.

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
| `GITHUB_TOKEN` | — | PAT with **Issues: write** on `GITHUB_BUG_REPO` (web only) |
| `GITHUB_BUG_REPO` | `phainestai/mimir` | Target repo for feedback issues |
| `BUG_REPORT_DRY_RUN` | — | If `1`/`true`, skip GitHub API |

### MCP Facade Container

| Variable | Default | Description |
|----------|---------|-------------|
| `MIMIR_SERVER_URL` | `http://web:8000` | FOB URL (local or hosted) |
| `MIMIR_DEV_ROOT` | — | Host dev folder for export/import; must match `-v` bind mount |
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
git pull && docker build -t mimir-web:local .
docker pull featurefactory/mimir-mcp:latest
# re-run with same docker run command above
```

## Troubleshooting

### Export reports success but no files on disk

The MCP container is missing a workspace bind mount. Add `MIMIR_DEV_ROOT` and a matching `-v` to your IDE MCP config (see [Filesystem tools](#filesystem-tools-export--import)). The tool now returns an error instead of silent failure when the mount is missing.

Do not use `$HOME:$HOME` — IDE JSON args are not shell-expanded, and Windows paths differ. Use an explicit dev-folder path.

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
