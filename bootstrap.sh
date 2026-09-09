#!/usr/bin/env bash
#
# Bring a fresh Omarchy install back to this machine's configuration.
# Idempotent: safe to re-run at any time, and the usual way to apply an edit.
#
#   ./bootstrap.sh
#
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

# ── Packages ────────────────────────────────────────────────────────────────
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

# ── Tests, before anything is installed ─────────────────────────────────────
# The input filter grabs the keyboard exclusively. A logic bug there is not a
# cosmetic problem, so nothing reaches /usr/local/bin unless the suite passes.
say "Input filter tests"
if ! python3 "$repo/k860-fix/test-filter.py" | tail -1 | grep -q '^ALL PASS'; then
  echo "  TESTS FAILED — refusing to install the input filter" >&2
  exit 1
fi
echo "  all assertions pass"

# ── Dotfiles ────────────────────────────────────────────────────────────────
# Symlinked, not copied, so edits under ~/.config show up in git status and
# cannot drift. Anything added under config/ is picked up with no script change.
say "Config symlinks"
while IFS= read -r -d '' src; do
  rel=${src#"$repo/config/"}
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
done < <(find "$repo/config" -type f -print0)

# ── K860 input filter ───────────────────────────────────────────────────────
say "k860-fix"
sudo install -Dm755 "$repo/k860-fix/k860-fix"         /usr/local/bin/k860-fix
sudo install -Dm644 "$repo/k860-fix/uinput.conf"      /etc/modules-load.d/uinput.conf
sudo install -Dm644 "$repo/k860-fix/k860-fix.service" /etc/systemd/system/k860-fix.service
sudo modprobe uinput || true
sudo systemctl daemon-reload
sudo systemctl enable k860-fix
sudo systemctl restart k860-fix
sleep 1
systemctl --no-pager --lines=4 status k860-fix || true

say "Done"
echo "  Hyprland picks up input.lua on its next reload: hyprctl reload"
echo "  Disable the input filter with: sudo systemctl disable --now k860-fix"
