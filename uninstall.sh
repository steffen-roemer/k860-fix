#!/bin/bash
# Remove k860-fix completely. Run: sudo ./uninstall.sh
set -uo pipefail
[[ $EUID -eq 0 ]] || { echo "run this with sudo" >&2; exit 1; }

systemctl disable --now k860-fix.service 2>/dev/null
rm -f /etc/systemd/system/k860-fix.service
rm -f /usr/local/bin/k860-fix
rm -f /etc/modules-load.d/uinput.conf
systemctl daemon-reload
echo "Removed. The K860 is ungrabbed and back to raw (faulty) behaviour."
