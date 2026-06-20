#!/usr/bin/env bash
# provision-factory-deps.sh — install dark-factory CLI tools (invoked by make provision).
#
# macOS: Homebrew packages
# Linux: apt packages when available (may require sudo)
# CI: skipped (GitHub Actions does not need tmux/fswatch for test jobs)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if [[ "${GITHUB_ACTIONS:-}" == "true" ]] || [[ "${CI:-}" == "true" ]]; then
  echo "provision-factory-deps: skipping system CLI install (CI environment)"
  exit 0
fi

install_brew_pkg() {
  local pkg="$1"
  if brew list "$pkg" >/dev/null 2>&1; then
    echo "brew: $pkg already installed"
  else
    echo "brew install $pkg …"
    brew install "$pkg"
  fi
}

install_apt_pkg() {
  local pkg="$1"
  if dpkg -s "$pkg" >/dev/null 2>&1; then
    echo "apt: $pkg already installed"
  else
    echo "apt install $pkg …"
    if command -v sudo >/dev/null 2>&1; then
      sudo apt-get install -y "$pkg"
    else
      apt-get install -y "$pkg"
    fi
  fi
}

echo "=== Installing dark-factory CLI dependencies ==="

if command -v brew >/dev/null 2>&1; then
  for pkg in gh fswatch tmux ripgrep util-linux jq; do
    install_brew_pkg "$pkg"
  done
  util_bin="$(brew --prefix util-linux 2>/dev/null)/bin"
  if [[ -x "${util_bin}/flock" ]]; then
    echo "flock: ${util_bin}/flock"
    if [[ ":${PATH}:" != *":${util_bin}:"* ]]; then
      echo "hint: add util-linux to PATH → export PATH=\"${util_bin}:\$PATH\""
    fi
  fi
elif command -v apt-get >/dev/null 2>&1; then
  # util-linux provides flock on Debian/Ubuntu; ripgrep package name is ripgrep
  for pkg in gh fswatch tmux ripgrep jq util-linux; do
    install_apt_pkg "$pkg" || echo "warn: could not install $pkg (continuing)"
  done
else
  echo "warn: no brew or apt-get — install manually: gh fswatch tmux ripgrep jq util-linux"
fi

echo "provision-factory-deps: done"
