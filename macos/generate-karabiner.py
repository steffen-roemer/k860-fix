#!/usr/bin/env python3
"""Generate macos/karabiner-k860.json from the pair table in ../k860-fix.

The Linux daemon is the source of truth: PAIRS, the pairing WINDOW, and the
Caps Lock chord all come from there, so the two platforms cannot drift apart.
The test suite runs this with --check and fails when the JSON is stale.

    python3 macos/generate-karabiner.py          rewrite the JSON
    python3 macos/generate-karabiner.py --check  exit 1 if the JSON is stale
"""
import importlib.machinery, importlib.util, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(HERE, "karabiner-k860.json")

spec = importlib.util.spec_from_loader(
    "k860", importlib.machinery.SourceFileLoader("k860", os.path.join(REPO, "k860-fix")))
k = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k)
e = k.e

# evdev code -> Karabiner "from"/"to" item. Extend when a new twin appears.
KEY = {
    e.KEY_D: {"key_code": "d"},
    e.KEY_KPSLASH: {"key_code": "keypad_slash"},
    e.KEY_3: {"key_code": "3"},
    e.KEY_KP8: {"key_code": "keypad_8"},
    e.KEY_8: {"key_code": "8"},
    e.KEY_KPMINUS: {"key_code": "keypad_hyphen"},
    e.KEY_Y: {"key_code": "y"},
    e.KEY_BACKSLASH: {"key_code": "backslash"},
    e.KEY_COMMA: {"key_code": "comma"},
    e.KEY_KP1: {"key_code": "keypad_1"},
    e.KEY_TAB: {"key_code": "tab"},
    e.KEY_PAGEUP: {"key_code": "page_up"},
    e.KEY_T: {"key_code": "t"},
    e.KEY_PREVIOUSSONG: {"consumer_key_code": "scan_previous_track"},
    e.KEY_DELETE: {"key_code": "delete_forward"},
    e.KEY_KPASTERISK: {"key_code": "keypad_asterisk"},
    e.KEY_B: {"key_code": "b"},
    e.BTN_MIDDLE: {"pointing_button": "button2"},
    e.KEY_COMPOSE: {"key_code": "application"},
    e.KEY_F: {"key_code": "f"},
    e.KEY_CAPSLOCK: {"key_code": "caps_lock"},
}

# Pairs whose twin was observed to arrive BEFORE the intended key on macOS.
# Karabiner's strict order must list the events as they actually come.
TWIN_FIRST = {(e.KEY_F, e.KEY_CAPSLOCK), (e.KEY_B, e.BTN_MIDDLE)}

# The keyboard as macOS sees it: over Bluetooth by its own id, through a
# Unifying receiver by the receiver's id.
DEVICES = [{"vendor_id": 1133, "product_id": 45913}, {"vendor_id": 1133, "product_id": 50475}]

# On macOS Find is Cmd+F, so plain Ctrl is free for the Caps Lock chord.
CAPS_CHORD_MODIFIERS = ["left_control"]

THRESHOLD_MS = int(round(k.WINDOW * 1000))


def manipulator(first, second, to, mandatory=None):
    modifiers = {"optional": ["any"]}
    if mandatory:
        modifiers = {"mandatory": list(mandatory), "optional": ["any"]}
    return {
        "type": "basic",
        "from": {
            "simultaneous": [dict(KEY[first]), dict(KEY[second])],
            "simultaneous_options": {"key_down_order": "strict"},
            "modifiers": modifiers,
        },
        "to": [dict(to)],
        "conditions": [{"type": "device_if", "identifiers": [dict(d) for d in DEVICES]}],
        "parameters": {"basic.simultaneous_threshold_milliseconds": THRESHOLD_MS},
    }


def build():
    manipulators = []
    for intended, companion in k.PAIRS:
        order = (companion, intended) if (intended, companion) in TWIN_FIRST else (intended, companion)
        if intended == k.CAPS_INTENDED and companion == k.CAPS_COMPANION:
            # The chord must precede the plain pair: Karabiner takes the first match.
            manipulators.append(manipulator(*order, KEY[e.KEY_CAPSLOCK], CAPS_CHORD_MODIFIERS))
        manipulators.append(manipulator(*order, KEY[intended]))
    return {
        "title": "Logitech ERGO K860 hardware fault repair",
        "rules": [{
            "description": "Logitech ERGO K860 - repair paired hardware faults",
            "manipulators": manipulators,
        }],
    }


def main():
    text = json.dumps(build(), indent=2, ensure_ascii=False) + "\n"
    if "--check" in sys.argv:
        current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if current != text:
            print("macos/karabiner-k860.json is stale: run python3 macos/generate-karabiner.py")
            return 1
        return 0
    open(OUT, "w", encoding="utf-8").write(text)
    print(f"wrote {os.path.relpath(OUT, REPO)}: {len(build()['rules'][0]['manipulators'])} manipulators")
    return 0


if __name__ == "__main__":
    sys.exit(main())
