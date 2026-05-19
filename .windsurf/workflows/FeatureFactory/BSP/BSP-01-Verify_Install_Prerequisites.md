# Activity: Verify & Install Prerequisites

**Activity ID**: 88
**Order**: 1
**Phase**: Elaboration
**Dependencies**: None

## Description

Verify & Install Prerequisites

## Guidance

# Verify & Install Prerequisites

## Objective

Read the Technology Stack Table from `docs/architecture/SAO.md`, check each tool on the developer's machine, install missing tools, and verify all versions meet minimum requirements. Must be **idempotent** — safe to run repeatedly.

---

## Process

### 1. Detect OS & Package Manager

```bash
# Detect OS
OS=$(uname -s)  # Darwin or Linux

# Detect package manager
if [[ "$OS" == "Darwin" ]]; then
    PKG_MGR="brew"
    # Verify Homebrew is installed
    command -v brew >/dev/null 2>&1 || {
        echo "ERROR: Homebrew not found. Install from https://brew.sh"
        exit 1
    }
elif [[ -f /etc/debian_version ]]; then
    PKG_MGR="apt"
elif [[ -f /etc/redhat-release ]]; then
    PKG_MGR="dnf"
else
    echo "ERROR: Unsupported OS. Requires macOS (Homebrew) or Linux (apt/dnf)."
    exit 1
fi
```

### 2. Read Technology Stack Table

Parse the Technology Stack Table from SAO.md. For each row:
1. Run the **Verify Command**
2. Compare installed version against **Version** requirement
3. If missing or below minimum: run the **Install Command** for the detected OS
4. If already installed and meets minimum: skip with ✅ message

### 3. Install Logic (Idempotent)

For each tool in the stack table:

```bash
check_and_install() {
    local tool="$1"
    local min_version="$2"
    local verify_cmd="$3"
    local install_cmd="$4"

    if eval "$verify_cmd" >/dev/null 2>&1; then
        local current_version=$(eval "$verify_cmd" 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?')
        echo "✅ $tool $current_version (required: $min_version)"
    else
        echo "📦 Installing $tool..."
        eval "$install_cmd"
        if eval "$verify_cmd" >/dev/null 2>&1; then
            echo "✅ $tool installed successfully"
        else
            echo "❌ Failed to install $tool"
            exit 1
        fi
    fi
}
```

### 4. Post-Install Verification

After all tools are installed, run a summary check:

```
Prerequisites Check Summary:
  Python     3.12.4  ✅ (required: 3.12+)
  Django     5.1.2   ✅ (required: 5.1+)
  Node.js    20.11.0 ✅ (required: 20+)
  npm        10.2.4  ✅ (required: 10+)
  git        2.43.0  ✅ (required: 2.x)
  make       4.4.1   ✅ (required: 4+)
  ruff       0.6.3   ✅ (required: 0.6+)
  pytest     8.3.1   ✅ (required: 8+)
  ...

All prerequisites satisfied. ✅
```

### 5. Handle Edge Cases

- **Homebrew not installed**: Error with install instructions, do not auto-install Homebrew
- **Permission errors**: Suggest `sudo` for system-level packages on Linux
- **Version conflicts**: Warn if installed version is newer than specified (should be fine) or if it's a different major version
- **Python virtual environment**: Do NOT create venv here — that's BSP-04's job
- **npm global packages**: Prefer local (npx) over global installs where possible

---

## Deliverables

- ✅ **OS & package manager** detected
- ✅ **All tools** from Technology Stack Table verified or installed
- ✅ **Version requirements** met for all tools
- ✅ **Summary report** printed
- ✅ **Idempotent** — safe to re-run

## Agent

None

## Skill

None

## Rules

None

## Artifacts Produced

None

## Artifacts Consumed

- **Makefile Template** (Code) - Optional

## Notes

No additional notes.
