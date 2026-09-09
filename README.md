# omarchy-setup

Machine configuration for a MacBookPro15,2 (T2) running [Omarchy](https://omarchy.org/).
Omarchy has no dotfiles mechanism of its own — `omarchy snapshot` is snapper, which
does not survive a reinstall — so this repo is the recovery path.

## Recovery after a reinstall

```bash
gh auth login
gh repo clone steffen-roemer/omarchy-setup ~/Work/omarchy-setup
~/Work/omarchy-setup/bootstrap.sh
```

`bootstrap.sh` is idempotent — it is also the normal way to apply an edit.

## What is in here

### `k860-fix/` — Logitech ERGO K860 double-key filter

The K860 (Bluetooth, `046d:b359`) has a hardware fault: ten physical keys emit a
second bogus event about 0.5 ms later.

| Physical key | Bogus companion | | Physical key | Bogus companion |
|---|---|---|---|---|
| `D` | `KP_SLASH`  | | `,`    | `KP1`           |
| `F` | `CAPSLOCK`  | | `Tab`  | `PAGEUP`        |
| `3` | `KP8`       | | `T`    | `PREVIOUSSONG`  |
| `8` | `KPMINUS`   | | `Entf` | `KPASTERISK`    |
| `Z` (`y`) | `BACKSLASH` | | `B` | `BTN_MIDDLE`  |

`k860-fix` is a Python/evdev daemon that grabs the K860's event nodes exclusively
and republishes a corrected stream on virtual uinput devices.

- **Only the K860.** Three independent gates — vendor, product, and a name
  containing `K860` — plus a never-touch list. Audit it with
  `sudo k860-fix devices`, which prints every input device and its verdict.
  The MacBook's internal keyboard is never grabbed, so it is always the way back in.
- **The intended key is never delayed.** Only the companion is held, and only
  until its partner arrives or the 30 ms window expires. Typing has no added latency;
  a *genuinely* pressed numpad key, Page Up, `#`, media key or middle click still
  works, delayed by the window.
- **`B` is cross-node.** `BTN_MIDDLE` lives on the Mouse node and `KEY_B` on the
  Keyboard node, so both are grabbed and fed into one ordered queue.
- **Caps Lock.** Physical `F` and physical Caps Lock emit an identical event pair,
  so they cannot be told apart. **Left Ctrl + Left Shift + that key** gives a real
  Caps Lock. It works by synthesising a Right Shift tap rather than emitting
  `KEY_CAPSLOCK`, because Omarchy runs `compose:caps` — `KEY_CAPSLOCK` would arm
  Compose instead. Note this makes `Ctrl+Shift+F` unavailable.

Kill switch, at any time:

```bash
sudo systemctl disable --now k860-fix     # keyboard reverts to raw behaviour
k860-fix/uninstall.sh                     # remove it entirely
```

**Run `python3 k860-fix/test-filter.py` before installing any edit.** It replays
real captured event sequences through the filter. A bad patch once crash-looped the
daemon; the resulting grab/ungrab race stranded a held key inside Hyprland and
flooded every window with `fffff…` until the keyboard was disconnected. Four guards
now cover that chain — fail-open on exceptions, `StartLimitBurst=5`,
release-on-teardown, and no grabbing while a key is held — but the tests are the
real safety net, and `bootstrap.sh` refuses to install if they fail.

### `config/hypr/input.lua` — German Macintosh layout

`kb_layout = "de"`, `kb_variant = "mac"`, natural touchpad scrolling.

`de(mac)` is the real Apple German layout: `@`, `|`, `{`, `[`, `~` sit where macOS
puts them. It includes `level3(ralt_switch)`, so **right Option is AltGr** — and
therefore the only one, since right Alt stops being Alt and left Alt becomes the
machine's only Alt key.

Do not try to put `@` on *left* Option. Apps universally treat Mod1 as a chord
modifier and Mod5 as a symbol modifier, and XKB's "consumed modifier" hint that
would bridge them is advisory and ignored in practice. `lv3:alt_switch` is never
the answer — it leaves zero Alt keys.

Consequences: `KEY_CAPSLOCK` is **Compose**, not Caps Lock; real Caps Lock is
**both Shifts together**. Omarchy's default `kb_options` is deliberately left
untouched. Only Hyprland is configured — the TTY and greeter would need
`localectl set-x11-keymap de pc105 mac`.
