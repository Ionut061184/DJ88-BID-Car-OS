#!/usr/bin/env python3
"""Owner-authorized QF001 55446 sharing opt-in. Preserve other OEM clients."""
import argparse
import json
import re
import subprocess
from pathlib import Path

PACKAGE = "ro.dj88bid.car.update5test"
KEY = PACKAGE + "KeyShareCarbodyState"
REGISTRY = "KeyAllPackages"
OEM = "com.qf.vehicle"
KEYS = (REGISTRY, KEY)

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

def clients(value):
    if value in ("null", ""):
        return []
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.]+(?:,[A-Za-z0-9_.]+)*,?", value):
        raise RuntimeError("Unexpected OEM registry; no change allowed")
    return [x for x in value.split(",") if x]

def validate(key, value):
    if key == REGISTRY:
        clients(value)
    elif key != KEY or value not in ("null", "0", "1"):
        raise RuntimeError("Unexpected setting value; no change allowed")

def read(serial, key):
    value = adb(serial, "shell", "settings", "get", "global", key)
    validate(key, value)
    return value

def snapshot(serial):
    return {k: read(serial, k) for k in KEYS}

def write(serial, key, value):
    validate(key, value)
    if value == "null":
        adb(serial, "shell", "settings", "delete", "global", key)
    else:
        # Empty-string argument must survive the remote shell.
        adb(serial, "shell", "settings", "put", "global", key, value if value else "''")
    if read(serial, key) != value:
        raise RuntimeError("Readback mismatch; keep backup for restoration")

def execute(serial, action, backup):
    verify(serial)
    before = snapshot(serial)
    if action == "check":
        return before
    if action == "enable":
        listed = clients(before[REGISTRY])
        registry = before[REGISTRY]
        if PACKAGE not in listed:
            registry = PACKAGE if not listed else registry.rstrip(",") + "," + PACKAGE
        after = {REGISTRY: registry, KEY: "1"}
        if before == after:
            return before
        with backup.open("x", encoding="utf-8") as f:
            json.dump({"serial": serial, "previous": before, "desired": after}, f)
            f.flush()
        for k in KEYS:
            if read(serial, k) != before[k]:
                raise RuntimeError("OEM settings changed concurrently; stop and inspect backup")
            if before[k] != after[k]:
                write(serial, k, after[k])
        return snapshot(serial)
    if action == "restore":
        state = json.loads(backup.read_text(encoding="utf-8"))
        if state.get("serial") != serial:
            raise RuntimeError("Backup belongs to another device")
        previous, desired = state.get("previous"), state.get("desired")
        if not isinstance(previous, dict) or not isinstance(desired, dict) or set(previous)!=set(KEYS) or set(desired)!=set(KEYS):
            raise RuntimeError("Invalid or legacy backup; do not overwrite OEM settings")
        for k in KEYS:
            validate(k, previous[k]); validate(k, desired[k])
            if before[k] not in (previous[k], desired[k]):
                raise RuntimeError("OEM state changed since activation; refuse to overwrite other clients")
        for k in reversed(KEYS):
            if read(serial, k) != before[k]:
                raise RuntimeError("Concurrent OEM change; stop restoration")
            if before[k] != previous[k]:
                write(serial, k, previous[k])
        return snapshot(serial)
    raise ValueError("Unknown action")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--serial", required=True)
    p.add_argument("--backup", type=Path, default=Path("bid-carbody-backup-v2.json"))
    p.add_argument("action", choices=["check","enable","restore"], default="check", nargs="?")
    a=p.parse_args()
    print("Only OEM sharing settings:", KEYS)
    print("Readback:", execute(a.serial,a.action,a.backup))
    print("Readback is not proof of live data. Use only while parked and disconnect ADB afterwards.")

if __name__=="__main__":
    main()
