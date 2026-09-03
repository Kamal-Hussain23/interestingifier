#!/usr/bin/env bash
# Interestingifier™ setup script.
#
# Installs the backend Python dependencies and Node 20 (which the frontend
# lint/test tooling needs — the Codio box ships an old Node 12).
# Safe to run again: it only installs what is missing.
#
# Usage: bash setup.sh

set -euo pipefail

# --- Backend dependencies -----------------------------------------------------
echo "Installing backend dependencies…"
pip install -r requirements.txt

# --- Node 20 via nvm ----------------------------------------------------------
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"

if [ ! -s "$NVM_DIR/nvm.sh" ]; then
  echo "Installing nvm…"
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
fi

# shellcheck disable=SC1091
source "$NVM_DIR/nvm.sh"

echo "Installing Node 20…"
nvm install 20
nvm use 20

# Symlink node/npm/npx into ~/bin (already on PATH) so every shell — including
# pre-commit's non-interactive runs — resolves Node 20 instead of the old 12.
mkdir -p "$HOME/bin"
NODE_VERSION="$(node -v)"
for tool in node npm npx; do
  ln -sf "$NVM_DIR/versions/node/$NODE_VERSION/bin/$tool" "$HOME/bin/$tool"
done

echo
echo "Setup complete!"
echo "node  => $(node --version)"
echo "npm   => $(npm --version)"