#!/usr/bin/env python3
"""Replay real captured K860 event sequences through Filter. Run: python3 test-filter.py"""
import importlib.util, importlib.machinery, os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_loader("k860",
        importlib.machinery.SourceFileLoader("k860", "k860-fix"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
e = m.e

class Sink:
    def __init__(s): s.out = []
    def write(s, t, c, v):
        if t == e.EV_KEY: s.out.append((c, v))
    def syn(s): pass

def run(seq, mods_before=(), window=0.030):
    sinks = [Sink(), Sink()]
    f = m.Filter([None, None], sinks, window=window)
    t = 0.0
    for code in mods_before:
        f.feed(0, m.evdev.InputEvent(0, 0, e.EV_KEY, code, 1), t); t += 0.001
    f.flush(t)
    for idx, code, val, dt in seq:
        t += dt
        f.feed(idx, m.evdev.InputEvent(0, 0, e.EV_KEY, code, val), t)
        f.flush(t)
    f.flush(t + 0.100)
    return sinks, f

def names(out): return [(m.key_name(c), v) for c, v in out]
ok = True
def check(label, got, want):
    global ok
    good = got == want; ok &= good
    print(f"{'PASS' if good else 'FAIL'}  {label}")
    if not good: print(f"        got  {got}\n        want {want}")

PRESS = lambda a, b: [(0, a, 1, 0), (0, b, 1, .0005), (0, a, 0, .130), (0, b, 0, .0006)]

for label, intended, companion in [
        ("3", e.KEY_3, e.KEY_KP8), ("8", e.KEY_8, e.KEY_KPMINUS),
        ("D", e.KEY_D, e.KEY_KPSLASH), ("Z(y)", e.KEY_Y, e.KEY_BACKSLASH),
        ("comma", e.KEY_COMMA, e.KEY_KP1), ("Tab", e.KEY_TAB, e.KEY_PAGEUP),
        ("T", e.KEY_T, e.KEY_PREVIOUSSONG), ("Entf", e.KEY_DELETE, e.KEY_KPASTERISK)]:
    s, f = run(PRESS(intended, companion))
    check(f"physical {label} -> single key", names(s[0].out),
          [(m.key_name(intended), 1), (m.key_name(intended), 0)])
    check("  no stuck keys", f.down, set())

s, f = run([(0, e.KEY_CAPSLOCK, 1, 0), (0, e.KEY_F, 1, .0005),
            (0, e.KEY_CAPSLOCK, 0, .112), (0, e.KEY_F, 0, .0007)])
check("physical F -> f only", names(s[0].out), [("KEY_F", 1), ("KEY_F", 0)])
check("  no stuck keys", f.down, set())

s, f = run([(1, e.BTN_MIDDLE, 1, 0), (0, e.KEY_B, 1, .0005),
            (1, e.BTN_MIDDLE, 0, .110), (0, e.KEY_B, 0, .0007)])
check("physical B -> b only (cross-node)", names(s[0].out), [("KEY_B", 1), ("KEY_B", 0)])
check("  middle click suppressed", names(s[1].out), [])

# Over the Unifying receiver the twin of B is the Menu key, ~20 ms behind.
s, f = run([(0, e.KEY_B, 1, 0), (0, e.KEY_COMPOSE, 1, .020),
            (0, e.KEY_B, 0, .100), (0, e.KEY_COMPOSE, 0, .020)], window=0.050)
check("physical B via receiver -> b only", names(s[0].out), [("KEY_B", 1), ("KEY_B", 0)])
check("  no stuck keys", f.down, set())

# A genuine Menu key on its own still gets through, just delayed by the window.
s, f = run([(0, e.KEY_COMPOSE, 1, 0), (0, e.KEY_COMPOSE, 0, .080)], window=0.050)
check("lone Menu key passes", names(s[0].out), [("KEY_COMPOSE", 1), ("KEY_COMPOSE", 0)])

CHORD = [(0, e.KEY_CAPSLOCK, 1, 0), (0, e.KEY_F, 1, .0005),
         (0, e.KEY_CAPSLOCK, 0, .112), (0, e.KEY_F, 0, .0007)]
MODS = (e.KEY_LEFTCTRL, e.KEY_LEFTSHIFT)

# Default: emit KEY_CAPSLOCK, correct wherever the Caps Lock key is not remapped.
m.CAPS_VIA_BOTH_SHIFT = False
s, f = run(CHORD, mods_before=MODS)
check("chord -> KEY_CAPSLOCK, no f", names(s[0].out),
      [("KEY_LEFTCTRL", 1), ("KEY_LEFTSHIFT", 1), ("KEY_CAPSLOCK", 1), ("KEY_CAPSLOCK", 0)])

# K860_CAPS_VIA_BOTH_SHIFT=1: synthesise the two-Shift gesture instead, for
# systems where KEY_CAPSLOCK has been remapped (e.g. compose:caps).
m.CAPS_VIA_BOTH_SHIFT = True
s, f = run(CHORD, mods_before=MODS)
check("chord -> RightShift tap, no f", names(s[0].out),
      [("KEY_LEFTCTRL", 1), ("KEY_LEFTSHIFT", 1), ("KEY_RIGHTSHIFT", 1), ("KEY_RIGHTSHIFT", 0)])
m.CAPS_VIA_BOTH_SHIFT = False

for label, code in [("numpad /", e.KEY_KPSLASH), ("Page Up", e.KEY_PAGEUP),
                    ("#/backslash", e.KEY_BACKSLASH), ("prev-track", e.KEY_PREVIOUSSONG),
                    ("numpad *", e.KEY_KPASTERISK)]:
    s, f = run([(0, code, 1, 0), (0, code, 0, .120)])
    check(f"solo {label} survives", names(s[0].out), [(m.key_name(code), 1), (m.key_name(code), 0)])

for label, mod in [("Super+F", e.KEY_LEFTMETA), ("Ctrl+F (Find)", e.KEY_LEFTCTRL)]:
    s, f = run([(0, e.KEY_CAPSLOCK, 1, 0), (0, e.KEY_F, 1, .0005),
                (0, e.KEY_CAPSLOCK, 0, .112), (0, e.KEY_F, 0, .0007)], mods_before=(mod,))
    check(f"{label} unaffected", names(s[0].out),
          [(m.key_name(mod), 1), ("KEY_F", 1), ("KEY_F", 0)])

print("\nALL PASS" if ok else "\nFAILURES ABOVE")
sys.exit(0 if ok else 1)
