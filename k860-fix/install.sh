#!/bin/bash
# Install k860-fix. Run: sudo ./install.sh
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "run this with sudo" >&2; exit 1; }
here=$(cd "$(dirname "$0")" && pwd)

install -Dm755 "$here/k860-fix"       /usr/local/bin/k860-fix
install -Dm644 "$here/uinput.conf"    /etc/modules-load.d/uinput.conf
install -Dm644 "$here/k860-fix.service" /etc/systemd/system/k860-fix.service

modprobe uinput || true
systemctl daemon-reload
systemctl enable --now k860-fix.service
systemctl --no-pager --lines=20 status k860-fix.service || true
echo
echo "Installed. Disable at any time with:  sudo systemctl stop k860-fix"
