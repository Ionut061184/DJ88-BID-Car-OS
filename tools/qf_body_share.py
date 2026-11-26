#!/usr/bin/env python3
"""Explicit, reversible QF001 body-sharing opt-in on an authorized ADB device."""
import argparse
import json
import re
import subprocess
from pathlib import Path

PACKAGE = "ro.dj88bid.car.update5test"
KEY = PACKAGE + "KeyShareCarbodyState"
OEM = "com.qf.vehicle"

def adb(serial, *args):
    if not re.fullmatch(r"[A-Za-z0-9_.:\[\]-]+", serial):
        raise ValueError("Invalid ADB serial")
    return subprocess.run(["adb", "-s", serial, *args], check=True,
                          capture_output=True, text=True, timeout=20).stdout.strip()

def verify(serial):
    if adb(serial, "get-state") != "device":
        raise RuntimeError("Device not authorized")
    for package in (OEM, PACKAGE):
        if not adb(serial, "shell", "pm", "path", package).startswith("package:"):
            raise RuntimeError("Required package missing: " + package)

def read(serial):
    result = adb(serial, "shell", "settings", "get", "global", KEY)
    if result not in ("null", "0", "1"):
        raise RuntimeError("Unexpected value; no change allowed")
    return result

def write(serial, value):
    if value == "null":
        adb(serial, "shell", "settings", "delete", "global", KEY)
    elif value in ("0", "1"):
        adb(serial, "shell", "settings", "put", "global", KEY, value)
    else:
        raise ValueError("Invalid saved value")
    if read(serial) != value:
        raise RuntimeError("Readback mismatch; keep backup for restoration")

def execute(serial, action, backup):
    verify(serial)
    before = read(serial)
    if action == "check":
        return before
    if action == "enable":
        if before == "1":
            return before  # do not replace existing backup or alter OEM state
        with backup.open("x", encoding="utf-8") as f:
            json.dump({"serial": serial, "key": KEY, "previous": before}, f)
            f.flush()
        write(serial, "1")
        return "1"
    if action == "restore":
        state = json.loads(backup.read_text(encoding="utf-8"))
        if state.get("serial") != serial or state.get("key") != KEY:
            raise RuntimeError("Backup belongs to a different device/key")
        value = state.get("previous")
        if value not in ("null", "0", "1"):
            raise RuntimeError("Invalid backup")
        write(serial, value)
        return value
    raise ValueError("Unknown action")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--serial", required=True, help="Exact authorized device serial from adb devices")
    p.add_argument("--backup", type=Path, default=Path("bid-carbody-backup.json"))
    p.add_argument("action", choices=["check", "enable", "restore"], default="check", nargs="?")
    args = p.parse_args()
    print("Only this global setting is addressed:", KEY)
    if args.action != "check":
        print("Run only on your own QF001 while parked. Backup:", args.backup)
    print("Readback:", execute(args.serial, args.action, args.backup))
    print("Readback alone does not prove reception of CAN data.")

if __name__ == "__main__":
    main()
