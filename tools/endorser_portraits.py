#!/usr/bin/env python3
"""
Endorser portrait pipeline for Christa's site.

Takes a raw photo, face-detects, crops to a consistent 4:5 head-and-shoulders
frame, and applies the shared gilt-toned monochrome curve so every endorser
portrait reads as one set regardless of source lighting/background.

Usage:
    python tools/endorser_portraits.py <input.jpg> assets/img/endorser-<slug>.jpg

Deps: pip install pillow opencv-python-headless numpy
Output: 400x500 JPEG, quality 85. Display target is ~60px wide in a gilt frame.
Backgrounds differ wildly across sources; the tone curve is what unifies them,
so run EVERY new endorser photo through this before adding it to the site.
"""
import sys, cv2, numpy as np
from PIL import Image, ImageOps

# gilt tritone: shadow -> gilt-deep -> gilt -> parchment  (matches site palette)
STOPS = [(0.0, (21, 16, 12)), (0.28, (74, 54, 26)), (0.55, (154, 120, 54)),
         (0.78, (200, 168, 102)), (1.0, (239, 228, 203))]


def build_lut():
    lut = np.zeros((256, 3), np.uint8)
    for i in range(256):
        t = i / 255
        for j in range(len(STOPS) - 1):
            a, ca = STOPS[j]; b, cb = STOPS[j + 1]
            if a <= t <= b:
                f = (t - a) / (b - a)
                lut[i] = [round(ca[k] + (cb[k] - ca[k]) * f) for k in range(3)]
                break
    return lut


def crop_45(im, box):
    W, H = im.size
    fx, fy, fw, fh = box
    cx, cy = fx + fw / 2, fy + fh / 2
    cw = 2.45 * fw
    ch = cw * 1.25
    if cw > W: cw = W; ch = cw * 1.25
    if ch > H: ch = H; cw = ch * 0.8
    left = max(0, min(cx - cw / 2, W - cw))
    top = max(0, min(cy - 0.95 * fh, H - ch))
    return im.crop((round(left), round(top), round(left + cw), round(top + ch)))


def detect_face(path):
    img = cv2.imread(path)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = sorted(cc.detectMultiScale(g, 1.1, 5, minSize=(60, 60)),
                   key=lambda b: b[2] * b[3], reverse=True)
    if not faces:
        raise SystemExit("No face detected; supply a manual box.")
    return tuple(int(v) for v in faces[0])


def main(src, dst):
    box = detect_face(src)
    im = Image.open(src).convert("RGB")
    c = crop_45(im, box)
    g = ImageOps.autocontrast(ImageOps.grayscale(c), cutoff=1)
    toned = Image.fromarray(build_lut()[np.asarray(g)], "RGB")
    toned.resize((400, 500), Image.LANCZOS).save(dst, quality=85, optimize=True)
    print("wrote", dst)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
