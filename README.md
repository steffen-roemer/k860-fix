# k860-fix

Some Logitech ERGO K860 keyboards develop a hardware fault where certain keys
emit **two** input events instead of one. Press `D` and you get `d/`. Press `3`
and you get `38`. Press `B` and something middle-clicks.

`k860-fix` is a small userspace daemon that grabs the keyboard's evdev nodes,
drops the bogus companion event, and republishes a corrected stream through
uinput. It runs below the display server, so it works identically on **Wayland,
X11, and a bare TTY**, on any distro with systemd.

It is a workaround, not a repair. If the keyboard is under warranty, claim it.

## Is this your problem?

The fault is deterministic: the bogus event lands ~0.5 ms after the real one,
always the same partner key. Watch the raw event stream:

```bash
sudo ./k860-fix diag        # does not grab; your keyboard keeps working
```

Press a suspect key. Two `EV_KEY … 1` lines for one keypress means yes.

## Requirements

`python3` and `python-evdev`:

| | |
|---|---|
| Arch | `pacman -S python-evdev` |
| Debian / Ubuntu | `apt install python3-evdev` |
| Fedora | `dnf install python3-evdev` |
| any | `pip install evdev` |

## Install

```bash
git clone https://github.com/orkitec/k860-fix
cd k860-fix
sudo ./install.sh
```

Turn it off at any time — this is instant and complete:

```bash
sudo systemctl disable --now k860-fix
sudo ./uninstall.sh          # or remove it entirely
```

## It only touches the K860

Losing the ability to type is the one failure mode worth being paranoid about,
so the daemon will not touch a device unless it clears **three independent
gates** — vendor `0x046D`, product `0xB359`, and a name containing `K860` —
plus an explicit never-touch list. Audit exactly what it will do, before
installing anything:

```bash
sudo ./k860-fix devices
```

It prints every input device on the system with a verdict and a reason. Your
built-in keyboard is never grabbed, so it is always the way back in.

## Adapting it to your keyboard

The faults are per-unit — yours may have a different set. The table near the
top of `k860-fix` is the whole configuration:

```python
PAIRS = [
    (e.KEY_D,      e.KEY_KPSLASH),      # physical D also emits numpad /
    (e.KEY_3,      e.KEY_KP8),
    (e.KEY_B,      e.BTN_MIDDLE),       # companion is on the Mouse node
    ...
]
```

Left is the key you meant, right is the bogus companion. Use `diag` to read off
the real code names, edit the list, then **run the tests before installing**:

```bash
python3 test-filter.py
```

The daemon holds an exclusive grab on your keyboard, so a bug in it is not
cosmetic — an early one crash-looped and stranded a held key inside the
compositor, flooding every window with `fffff…`. The suite replays captured
event sequences and checks each pair collapses, each companion still works
alone, and nothing is ever left held.

## Settings

Optional, in `/etc/default/k860-fix`:

| Variable | Default | |
|---|---|---|
| `K860_WINDOW` | `0.030` | Pairing window, seconds. The observed gap is ~0.5 ms, so this has wide margin. |
| `K860_CAPS_ESCAPE` | `LEFTCTRL,LEFTSHIFT` | Modifiers that turn the ambiguous Caps/F key into a real Caps Lock. |
| `K860_CAPS_VIA_BOTH_SHIFT` | unset | Set to `1` if your XKB options remap the Caps Lock key — see below. |
| `K860_UNIQ` | unset | Pin to one keyboard by Bluetooth MAC. Only needed if you own two. |

### The Caps Lock complication

On this fault, physical `F` and physical `Caps Lock` emit an **identical** event
pair (`KEY_CAPSLOCK` + `KEY_F`). They cannot be told apart from the event stream,
so the common case wins: that pair becomes `f`. Holding `K860_CAPS_ESCAPE` while
pressing it gives a real Caps Lock instead.

Whatever you choose for that chord becomes unavailable with `F`, so avoid
`Ctrl` alone — `Ctrl+F` is Find nearly everywhere.

If your setup remaps the Caps Lock key (e.g. `compose:caps`, common on
Omarchy), emitting `KEY_CAPSLOCK` would trigger *that* instead. Set
`K860_CAPS_VIA_BOTH_SHIFT=1` and the daemon synthesises a Right Shift tap
instead, which resolves to `Caps_Lock` under `shift:both_capslock`.

## macOS

This daemon is Linux-only — it depends on evdev and uinput. On macOS the same
repair is done with [Karabiner-Elements](https://karabiner-elements.pqrs.org/),
and a ready-made rule covering all ten pairs is in
[`macos/karabiner-k860.json`](macos/karabiner-k860.json):

```bash
cp macos/karabiner-k860.json ~/.config/karabiner/assets/complex_modifications/
```

Then enable it in Karabiner-Elements under *Complex Modifications → Add rule*.

It uses the same approach — `simultaneous` with a 30 ms threshold, scoped to
`vendor_id 1133 / product_id 45913`, which is `0x046D:0xB359` in the hex the
Linux side uses. Those ids survive Bluetooth unchanged on both platforms.

Two differences worth knowing if you run both:

- **The Caps Lock escape is `left_control` there, not `Ctrl+Shift`.** On macOS
  Find is `Cmd+F`, so `Ctrl+F` is free. On Linux `Ctrl+F` is Find nearly
  everywhere, so the Linux default moves the chord out of the way.
- **Karabiner needs `key_down_order: strict`**, which documents the arrival
  order per pair: `caps_lock` before `f`, but the intended key first in all nine
  others. This daemon handles either order, but the asymmetry is real — it shows
  up identically in Linux event captures.

## How it works

**The key you meant is never delayed.** Only the bogus companion is held, and
only until its partner arrives or the window expires — so typing has no added
latency, while a *genuinely* pressed numpad key, Page Up, `#`, media key or
middle click still works, delayed by the window. Events are queued in arrival
order, so a held companion briefly blocks what follows rather than being
overtaken.

**Some faults span devices.** `BTN_MIDDLE` lives on the keyboard's Mouse node
while `KEY_B` is on its Keyboard node, so every node is grabbed and merged into
one ordered queue, then republished to matching virtual devices.

**It fails safe.** It creates its uinput devices before grabbing anything, waits
for all keys to be released before taking the grab, releases everything it
emitted on shutdown, and forwards events untouched if the filter itself throws.

## Layout

```
k860-fix            the daemon
k860-fix.service    systemd unit
uinput.conf         /etc/modules-load.d entry
install.sh          uninstall.sh
test-filter.py      run this before installing an edit
macos/              equivalent Karabiner-Elements rule
personal/           the author's machine, as a worked example
```

## Licence

MIT.

---

Made by [Orkitec](https://github.com/orkitec).
