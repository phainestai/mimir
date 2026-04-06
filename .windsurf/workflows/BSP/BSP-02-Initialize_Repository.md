# Activity: Initialize Repository

**Activity ID**: TBD
**Order**: 2
**Phase**: Initialize
**Dependencies**: Predecessor: BSP-01 (Verify & Install Prerequisites)

## Description

Initialize Repository

## Guidance

# Initialize Repository

## Objective

Create a new Git repository with essential root-level files: `.gitignore`, `README.md`, `LICENSE`, and initial commit.

---

## Process

### 1. Initialize Git

```bash
git init
git branch -M main
```

### 2. Create .gitignore

Generate a `.gitignore` tailored to the technology stack from SAO.md. Include patterns for:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
.venv/
venv/
*.egg

# Node.js
node_modules/
npm-debug.log*

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local
.env.*.local

# Database
*.sqlite3
db.sqlite3

# Logs
logs/
*.log

# Coverage
htmlcov/
.coverage
.coverage.*
coverage.xml

# Build artifacts
staticfiles/
media/
```

Adapt based on actual stack decisions in SAO.md.

### 3. Create README.md

```markdown
# {Project Name}

{One-sentence description from ESM user journey}

## Quick Start

\`\`\`bash
make provision   # Install prerequisites & dependencies
make run         # Start development server
\`\`\`

Then open http://localhost:8000 in your browser.

## Development

| Command          | Description                    |
|------------------|--------------------------------|
| `make provision` | Install all prerequisites      |
| `make run`       | Start development server       |
| `make test`      | Run all tests                  |
| `make lint`      | Run linter                     |
| `make format`    | Auto-format code               |
| `make clean`     | Remove build artifacts         |
| `make help`      | Show all available targets     |

## Documentation

- [System Architecture Overview](docs/architecture/SAO.md)
- [Modus Operandi](docs/process/MODUS_OPERANDI.md)
```

### 4. Create LICENSE

Choose license based on project requirements. Default to MIT unless SAO.md specifies otherwise.

### 5. Initial Commit

```bash
git add .
git commit -m "chore(init): initialize repository with .gitignore, README, LICENSE"
```

---

## Deliverables

- ✅ **Git repository** initialized on `main` branch
- ✅ **.gitignore** created for project stack
- ✅ **README.md** with Quick Start and Makefile target table
- ✅ **LICENSE** file created
- ✅ **Initial commit** made

## Artifacts Produced

- `.gitignore`
- `README.md`
- `LICENSE`

## Artifacts Consumed

- `docs/architecture/SAO.md` — Technology Stack Table (for .gitignore patterns)
- ESM artifacts — project name and description (for README)

## Notes

No additional notes.
