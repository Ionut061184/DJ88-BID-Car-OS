"""Fail-closed check of original Build 14 assets before Update 3 integration.
Run from repository root: python tools/verify_build14_base.py
This is not an APK builder and does not establish native equivalence.
"""
import hashlib
from pathlib import Path

EXPECTED = {
    "bid_approved.png": "0e98e109b4402fdece4a4dcefeff287e4414ee5487f7e7b8d7e0f9e5cffd31fe",
    "bid_fullbleed.png": "e7eb12698d98d64ce14a42d39f13901127204eb396553cf12a0b85992a6bd2b1",
    "bid_adaptive.js": "0a45d7f1c2ce9d1a50621c45a44a7cacef12d2c47a87e351d52d0f761e553f97",
    "bid_runtime.js": "b69a43120a9fabee733ef3cc9eb8a70105e341f9ff6bdb4254f268ea3c4438ad",
    "bid_status.js": "dab1013537b89d493efc3131866dc58fe0c4deabdece410787590b3cae824ea8",
    "bid_status.css": "2bddd0fdb69d23029938d1512959310e9d451d77f3659ff681a871a73d9a17c8",
    "index.html": "1b62a4b473dad9cdb39320a2b26cb033dfec3024987e4c2076319f52ed44c506",
}

def main():
    root = Path(__file__).resolve().parents[1] / "app/src/main/assets"
    failures = []
    for name, expected in EXPECTED.items():
        path = root / name
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "MISSING"
        passed = actual == expected
        print(f"{'OK' if passed else 'FAIL'} {name}: {actual}")
        if not passed:
            failures.append(name)
    if failures:
        raise SystemExit("STOP: Build 14 baseline mismatch; do not publish an update.")
    print("Asset baseline matches. Native source, signing and device tests still required.")

if __name__ == "__main__":
    main()
