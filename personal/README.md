# personal/

The author's machine setup — an Omarchy (Arch + Hyprland) MacBookPro15,2 — kept
here as a **worked example** rather than as anything you need.

`k860-fix` itself is configured entirely through `/etc/default/k860-fix` and
installs with `../install.sh` on any systemd distro. Nothing in this directory
is required to use it.

| File | What it is |
|---|---|
| `default-k860-fix` | The settings that make the Caps Lock chord work under Omarchy's `compose:caps`. Installed to `/etc/default/k860-fix`. |
| `bootstrap.sh` | Packages, tests, dotfile symlinks, then `../install.sh`. Idempotent. |
| `config/hypr/input.lua` | German Macintosh XKB layout and natural scrolling. Unrelated to the keyboard fault. |

To adapt it: copy this directory, replace `config/` with your own dotfiles, and
change the `pacman` line to your package manager.
