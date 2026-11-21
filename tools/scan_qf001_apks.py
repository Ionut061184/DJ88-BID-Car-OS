#!/usr/bin/env python3
"""Inventariază APK-urile QF001 fără a modifica firmware-ul.

Rulare:
    python3 tools/scan_qf001_apks.py /cale/catre/system --output qf001-apks.json
Opțional: Android SDK aapt/aapt2 instalat pentru metadate reale din manifest.

Nu lansează aplicații OEM, nu rescrie APK-uri, nu montează și nu flash-uiește imagini.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

KEYWORDS = {
    "radio": ("radio", "tuner", "fmradio", "fm_radio"),
    "bluetooth_auto": ("bluetooth", "bth", "btphone", "bt_music", "handsfree", "phonelink"),
    "muzica": ("music", "media", "audio", "player"),
    "dsp": ("dsp", "equalizer", "equaliser", "soundeffect", "sound_effect"),
}
APK_LIMIT = 10000


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_badging(apk: Path, executable: str | None) -> dict:
    if not executable:
        return {"status": "aapt_indisponibil"}
    try:
        p = subprocess.run([executable, "dump", "badging", str(apk)],
                           text=True, capture_output=True, timeout=25, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return {"status": "eroare_aapt"}
    if p.returncode:
        return {"status": "manifest_necitit", "stderr": p.stderr[:400]}
    package = re.search(r"^package: name='([^']+)'", p.stdout, re.MULTILINE)
    launch = re.findall(r"^launchable-activity: name='([^']+)'", p.stdout, re.MULTILINE)
    label = re.search(r"^application-label: '([^']*)'", p.stdout, re.MULTILINE)
    return {
        "status": "manifest_citit",
        "package": package.group(1) if package else None,
        "launchable_activities": launch,
        "app_label": label.group(1) if label else None,
    }


def scan(root: Path, aapt: str | None) -> list[dict]:
    items = []
    for apk in sorted(root.rglob("*"), key=lambda p: str(p).lower()):
        if not apk.is_file() or apk.suffix.lower() != ".apk":
            continue
        if len(items) >= APK_LIMIT:
            raise RuntimeError("Prea multe APK-uri; inventarul a fost oprit.")
        manifest = read_badging(apk, aapt)
        search = " ".join(str(value) for value in (
            apk.name, str(apk.parent), manifest.get("package"), manifest.get("app_label")
        )).lower()
        kinds = [kind for kind, words in KEYWORDS.items()
                 if any(word in search for word in words)]
        items.append({
            "relative_path": str(apk.relative_to(root)),
            "bytes": apk.stat().st_size,
            "sha256": hash_file(apk),
            "candidate_for": kinds,
            "identification": "posibil_dupa_nume" if kinds else "neclasificat",
            "manifest": manifest,
            "qf001_function_verified": False,
        })
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("system_dir", type=Path, help="Directorul /system extras din QF001")
    parser.add_argument("--output", type=Path, default=Path("qf001-apks.json"))
    parser.add_argument("--aapt", help="Calea către Android SDK aapt; altfel caută în PATH")
    args = parser.parse_args()
    root = args.system_dir.resolve()
    if not root.is_dir():
        parser.error("Este necesar un director extras, nu un system.img.")
    aapt = args.aapt or shutil.which("aapt")
    if aapt and not Path(aapt).is_file() and not shutil.which(aapt):
        parser.error("Executabilul aapt nu există.")
    items = scan(root, aapt)
    report = {
        "system_directory": str(root),
        "apk_total": len(items),
        "aapt_used": aapt or None,
        "warning": "Potrivirea după nume NU confirmă funcția QF001; manifestul citit nu dovedește că un APK este lansabil fără privilegii.",
        "apks": items,
    }
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    matched = sum(bool(x["candidate_for"]) for x in items)
    print(f"Inventar: {len(items)} APK-uri; {matched} candidați; raport {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
