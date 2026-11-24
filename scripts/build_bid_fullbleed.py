"""Derive a full-width 1280x720 BID image from the approved, immutable PNG.

The middle 700 columns (x=300..999) are copied pixel-for-pixel: the vehicle is
never resized or geometrically distorted. Only two narrow non-vehicle
architectural strips are expanded to replace the baked-in side margins.
Coordinate mapping in bid_status.js must match these source/destination knots.
"""
from pathlib import Path
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "app/src/main/assets/bid_approved.png"
DEST = ROOT / "app/src/main/assets/bid_fullbleed.png"

def main():
    src = Image.open(SRC).convert("RGBA")
    if src.size != (1280, 720):
        raise ValueError("BID approved artwork dimensions changed")
    out = Image.new("RGBA", (1280, 720))
    pieces = (
        ((100, 0, 255, 720), 0, 155),
        ((255, 0, 300, 720), 155, 145),
        ((300, 0, 1000, 720), 300, 700),
        ((1000, 0, 1035, 720), 1000, 135),
        ((1035, 0, 1180, 720), 1135, 145),
    )
    for crop, dst_x, dst_w in pieces:
        part = src.crop(crop)
        if part.width != dst_w:
            part = part.resize((dst_w, 720), Image.Resampling.BICUBIC)
        out.paste(part, (dst_x, 0))
    if ImageChops.difference(src.crop((300, 0, 1000, 720)),
                             out.crop((300, 0, 1000, 720))).getbbox():
        raise AssertionError("The center/vehicle was modified")
    out.save(DEST, optimize=True)
    print("Full-bleed BID ready; central vehicle pixel-identical")

if __name__ == "__main__":
    main()
