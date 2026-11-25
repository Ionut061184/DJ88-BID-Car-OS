"""Import the verified cumulative Update 3 archive into this branch.

Run from repository root:
  python tools/import_update3.py /path/to/DJ88-BID-Update3-Etapa8-System-candidat.zip
Review git diff before committing. This tool does not build or sign an APK.
"""
import hashlib
import sys
from pathlib import Path
from zipfile import ZipFile

ARCHIVE = "212546bfec80e10d91ae1631ccc6c3c8679da90eafb3b90ee4182eb986cc4e3a"
MASTER = {
    "bid_approved.png": "0e98e109b4402fdece4a4dcefeff287e4414ee5487f7e7b8d7e0f9e5cffd31fe",
    "bid_fullbleed.png": "e7eb12698d98d64ce14a42d39f13901127204eb396553cf12a0b85992a6bd2b1",
    "bid_adaptive.js": "0a45d7f1c2ce9d1a50621c45a44a7cacef12d2c47a87e351d52d0f761e553f97",
    "bid_runtime.js": "b69a43120a9fabee733ef3cc9eb8a70105e341f9ff6bdb4254f268ea3c4438ad",
    "bid_status.js": "dab1013537b89d493efc3131866dc58fe0c4deabdece410787590b3cae824ea8",
    "bid_status.css": "2bddd0fdb69d23029938d1512959310e9d451d77f3659ff681a871a73d9a17c8",
}
MODULES = ("bid_smart.js", "bid_trip.js", "bid_battery.js", "bid_sound.js", "bid_vision.js",
           "bid_diagnostics.js", "bid_themes.js", "bid_system.js", "index.html")

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    root = Path(__file__).resolve().parents[1]
    dest = root / "app/src/main/assets"
    if not dest.is_dir():
        raise SystemExit("Not an Android source checkout")
    archive = Path(sys.argv[1])
    if sha(archive.read_bytes()) != ARCHIVE:
        raise SystemExit("STOP: incorrect candidate archive")
    with ZipFile(archive) as z:
        data = {name: z.read("assets/" + name) for name in (*MASTER, *MODULES)}
        for name, expected in MASTER.items():
            if sha(data[name]) != expected:
                raise SystemExit("STOP: original Build 14 asset mismatch: " + name)
        test_source = z.read("test_status.py")
    # Never extract arbitrary archive paths. Write only the explicitly allowed files.
    for name, payload in data.items():
        (dest / name).write_bytes(payload)
    # The browser regression script expects an assets/ sibling: keep a reproducible
    # test location using a small staging copy, rather than changing its behavior.
    suite = root / "tests/update3_browser"
    suite.mkdir(parents=True, exist_ok=True)
    (suite / "test_status.py").write_bytes(test_source)
    print("Imported verified Build 14 artwork and eight Update 3 modules.")
    print("Browser tests: copy app/src/main/assets to tests/update3_browser/assets, then run test_status.py.")
    print("Review existing CI artwork guard; do not disable it. Native compile, signature comparison and device tests still required.")

if __name__ == "__main__":
    main()
