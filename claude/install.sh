#!/bin/bash
# Link hikari-claude.json into Claude Code's themes folder and make it the
# active theme. Claude Code watches the folder, so open sessions pick it up.
# It needs only bash and jq, so it works with or without Omarchy.

set -euo pipefail

dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
config_dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
settings="$config_dir/settings.json"

mkdir -p "$config_dir/themes"
ln -sfn "$dir/hikari-claude.json" "$config_dir/themes/hikari-claude.json"

if [[ -f $settings ]]; then
  if ! command -v jq >/dev/null; then
    echo "install.sh needs jq to edit $settings" >&2
    exit 1
  fi
  tmp=$(mktemp "$settings.XXXXXX")
  jq '.theme = "custom:hikari-claude"' "$settings" >"$tmp"
  mv "$tmp" "$settings"
else
  printf '{\n  "theme": "custom:hikari-claude"\n}\n' >"$settings"
fi

echo "hikari-claude is linked and active in $settings"
