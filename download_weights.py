"""
Run this ONCE to download DeepFace Facenet weights:
    python download_weights.py
"""
import os, requests, sys

WEIGHTS_DIR  = os.path.join(os.path.expanduser("~"), ".deepface", "weights")
WEIGHTS_FILE = os.path.join(WEIGHTS_DIR, "facenet_weights.h5")
URL = "https://github.com/serengil/deepface_models/releases/download/v1.0/facenet_weights.h5"

os.makedirs(WEIGHTS_DIR, exist_ok=True)

# Delete old/corrupt file
if os.path.exists(WEIGHTS_FILE):
    mb = os.path.getsize(WEIGHTS_FILE) / 1024 / 1024
    print(f"Found existing file: {mb:.1f} MB — deleting and re-downloading...")
    os.remove(WEIGHTS_FILE)

print(f"Downloading Facenet weights (~92 MB)...")
print(f"Saving to: {WEIGHTS_FILE}")

try:
    with requests.get(URL, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done  = 0
        with open(WEIGHTS_FILE, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                f.write(chunk)
                done += len(chunk)
                pct = done / total * 100 if total else 0
                bar = "#" * int(pct / 2)
                sys.stdout.write(f"\r  [{bar:<50}] {pct:.1f}%  ({done//1024//1024} MB)")
                sys.stdout.flush()
    print(f"\n\nDone! File size: {os.path.getsize(WEIGHTS_FILE)/1024/1024:.1f} MB")
    print("Now run:  python app.py")
except Exception as e:
    print(f"\nDownload failed: {e}")
    print("Try downloading manually from:")
    print(URL)
    print(f"And place it at: {WEIGHTS_FILE}")
