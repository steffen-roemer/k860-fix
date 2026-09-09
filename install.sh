#!/bin/bash
#
# Install k860-fix as a system service. Works on any systemd distro.
#
#   sudo ./install.sh
#
# Requires python3 and python-evdev:
#   Arch           pacman -S python-evdev
#   Debian/Ubuntu  apt install python3-evdev
#   Fedora         dnf install python3-evdev
#   any            pip install evdev
#
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "run this with sudo" >&2; exit 1; }
here=$(cd "$(dirname "$0")" && pwd)

python3 -c 'import evdev' 2>/dev/null || {
  echo "python-evdev is not installed; see the header of this script" >&2
  exit 1
}

install -Dm755 "$here/k860-fix"         /usr/local/bin/k860-fix
install -Dm644 "$here/uinput.conf"      /etc/modules-load.d/uinput.conf
install -Dm644 "$here/k860-fix.service" /etc/systemd/system/k860-fix.service

modprobe uinput || true
systemctl daemon-reload
systemctl enable k860-fix.service
systemctl restart k860-fix.service
sleep 1
systemctl --no-pager --lines=6 status k860-fix.service || true

cat <<'MSG'

Installed. Useful commands:

  sudo k860-fix devices          which input devices this will and will not touch
  sudo k860-fix diag             watch raw events (does not grab; safe)
  journalctl -u k860-fix -f      what it is deciding
  sudo systemctl disable --now k860-fix    turn it off

Machine-local settings go in /etc/default/k860-fix; see personal/ for an example.
MSG
