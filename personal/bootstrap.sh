#!/usr/bin/env bash
#
# Set up the author's machine: an Omarchy (Arch) MacBookPro15,2.
#
# This is a worked example, not a requirement -- k860-fix itself installs with
# ../install.sh on any systemd distro. Copy this directory, drop in your own
# config, and adjust the package manager line.
#
# Idempotent: safe to re-run, and the normal way to apply an edit.
#
set -euo pipefail

personal=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo=$(cd "$personal/.." && pwd)
say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

say "Packages"
missing=()
for p in python-evdev evtest; do
  pacman -Qq "$p" &>/dev/null || missing+=("$p")
done
if ((${#missing[@]})); then
  sudo pacman -S --needed --noconfirm "${missing[@]}"
else
  echo "  all present"
fi

# The filter takes an exclusive grab on the keyboard, so a logic bug there is
# not cosmetic. Nothing reaches /usr/local/bin unless the suite passes.
say "Input filter tests"
if ! python3 "$repo/test-filter.py" | tail -1 | grep -q '^ALL PASS'; then
  echo "  TESTS FAILED — refusing to install the input filter" >&2
  exit 1
fi
echo "  all assertions pass"

# Symlinked, not copied, so edits under ~/.config show up in git status and
# cannot drift. Anything added under personal/config/ is picked up with no
# change to this script.
say "Config symlinks"
while IFS= read -r -d '' src; do
  rel=${src#"$personal/config/"}
  dst="$HOME/.config/$rel"
  mkdir -p "$(dirname "$dst")"
  if [[ -L $dst && $(readlink -f "$dst") == "$(readlink -f "$src")" ]]; then
    echo "  ok    ~/.config/$rel"
    continue
  fi
  if [[ -e $dst && ! -L $dst ]]; then
    bak="$dst.bak.$(date +%s)"
    mv "$dst" "$bak"
    echo "  saved ~/.config/$rel -> $(basename "$bak")"
  fi
  ln -sfn "$src" "$dst"
  echo "  link  ~/.config/$rel"
done < <(find "$personal/config" -type f -print0)

say "k860-fix"
sudo install -Dm644 "$personal/default-k860-fix" /etc/default/k860-fix
sudo "$repo/install.sh"

say "Done"
echo "  Hyprland picks up input.lua on its next reload: hyprctl reload"
echo "  Disable the input filter with: sudo systemctl disable --now k860-fix"
