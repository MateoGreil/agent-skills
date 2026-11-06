#!/usr/bin/env python3
"""Own the X11/Wayland clipboard with two flavors: text/html + plain-text TSV.

Keeps running to serve paste requests (like the macOS clipboard does natively).
Usage: clip_table.py <table.html> <table.tsv>
"""
import os
import sys
from pathlib import Path

import gi

gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GLib

html_bytes = Path(sys.argv[1]).read_bytes()
tsv_bytes = Path(sys.argv[2]).read_bytes()

display = Gdk.Display.get_default()
if display is None:
    display = Gdk.Display.open(os.environ.get("DISPLAY", ":0"))
if display is None:
    sys.exit("Error: no display available")

provider = Gdk.ContentProvider.new_union([
    Gdk.ContentProvider.new_for_bytes("text/html", GLib.Bytes.new(html_bytes)),
    Gdk.ContentProvider.new_for_bytes(
        "text/plain;charset=utf-8", GLib.Bytes.new(tsv_bytes)
    ),
    Gdk.ContentProvider.new_for_bytes("text/plain", GLib.Bytes.new(tsv_bytes)),
])
if not display.get_clipboard().set_content(provider):
    sys.exit("Error: could not take clipboard ownership")

print("Serving clipboard (text/html + text/plain). Ctrl+C to stop.", flush=True)
GLib.MainLoop().run()
