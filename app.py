import os, uuid, base64, cv2, numpy as np, pandas as pd, requests
from flask import Flask, request, jsonify, render_template, send_from_directory

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER   = os.path.join(BASE_DIR, "uploads")
DATABASE_FOLDER = os.path.join(BASE_DIR, "database")
IMAGES_FOLDER   = os.path.join(BASE_DIR, "suspect_images")
CSV_PATH        = os.path.join(DATABASE_FOLDER, "suspects.csv")
ALLOWED_EXT     = {"png", "jpg", "jpeg", "webp"}
TOP_N_RESULTS   = 8
HF_API_TOKEN    = ""

os.makedirs(UPLOAD_FOLDER,   exist_ok=True)
os.makedirs(DATABASE_FOLDER, exist_ok=True)
os.makedirs(IMAGES_FOLDER,   exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"]      = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# ── DeepFace init ─────────────────────────────────────────────────────────────
DEEPFACE_AVAILABLE = False
DeepFace = None
WEIGHTS_FILE = os.path.join(os.path.expanduser("~"), ".deepface", "weights", "facenet_weights.h5")

def _try_init_deepface():
    global DEEPFACE_AVAILABLE, DeepFace
    try:
        if os.path.exists(WEIGHTS_FILE):
            mb = os.path.getsize(WEIGHTS_FILE) / 1024 / 1024
            if mb < 80:
                os.remove(WEIGHTS_FILE)
                print(f"[INFO] Deleted corrupted weights ({mb:.1f} MB)")
        from deepface import DeepFace as _DF
        tmp = os.path.join(UPLOAD_FOLDER, "_test.jpg")
        dummy = np.ones((160, 160, 3), dtype=np.uint8) * 100
        cv2.imwrite(tmp, dummy)
        _DF.verify(tmp, tmp, model_name="Facenet",
                   detector_backend="opencv", enforce_detection=False)
        os.remove(tmp)
        DeepFace = _DF
        DEEPFACE_AVAILABLE = True
        print("[INFO] ✅ DeepFace/Facenet ready")
    except Exception as e:
        DEEPFACE_AVAILABLE = False
        print(f"[INFO] DeepFace unavailable — using ORB fallback")
        print("[INFO] Run  python download_weights.py  to enable neural matching")

_try_init_deepface()

# ── Helpers ───────────────────────────────────────────────────────────────────
def allowed_file(fn):
    return "." in fn and fn.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def load_database():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Database not found: {CSV_PATH}")
    return pd.read_csv(CSV_PATH, dtype=str).fillna("N/A")

def extract_face(path):
    img = cv2.imread(path)
    if img is None:
        return None
    gray  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(40, 40))
    if len(faces):
        x, y, w, h = faces[0]
        pad = int(0.15 * min(w, h))
        x1 = max(0, x-pad); y1 = max(0, y-pad)
        x2 = min(img.shape[1], x+w+pad); y2 = min(img.shape[0], y+h+pad)
        crop = img[y1:y2, x1:x2]
        return crop if crop.size > 0 else img
    return img

def orb_similarity(p1, p2):
    try:
        f1 = extract_face(p1)
        f2 = extract_face(p2)
        if f1 is None or f2 is None:
            return None
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        g1 = clahe.apply(cv2.cvtColor(cv2.resize(f1, (200, 200)), cv2.COLOR_BGR2GRAY))
        g2 = clahe.apply(cv2.cvtColor(cv2.resize(f2, (200, 200)), cv2.COLOR_BGR2GRAY))
        orb = cv2.ORB_create(nfeatures=500)
        kp1, des1 = orb.detectAndCompute(g1, None)
        kp2, des2 = orb.detectAndCompute(g2, None)
        if des1 is None or des2 is None or len(des1) < 5 or len(des2) < 5:
            diff = cv2.absdiff(g1, g2).astype(np.float32)
            return float(round(max(0.0, (1.0 - diff.mean() / 128.0)) * 100.0, 1))
        bf      = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = sorted(bf.match(des1, des2), key=lambda x: x.distance)
        good    = [m for m in matches if m.distance < 60]
        ratio   = len(good) / min(len(kp1), len(kp2))
        avg_d   = np.mean([m.distance for m in matches[:20]])
        score   = (ratio * 0.6 + max(0.0, 1.0 - avg_d/256.0) * 0.4) * 100.0
        return float(round(min(99.0, max(0.0, score)), 1))
    except Exception as e:
        print(f"  [WARN] ORB failed: {e}")
        return None

def compare_deepface(p1, p2):
    try:
        r    = DeepFace.verify(img1_path=p1, img2_path=p2,
                               model_name="Facenet", detector_backend="opencv",
                               enforce_detection=False, align=True)
        dist = float(r["distance"])
        thr  = float(r["threshold"])
        return float(round(max(0.0, (1.0 - dist / thr)) * 100.0, 1))
    except Exception as e:
        print(f"  [WARN] DeepFace error: {e}")
        return None

def compare_faces(p1, p2):
    if DEEPFACE_AVAILABLE:
        s = compare_deepface(p1, p2)
        if s is not None:
            return s
    return orb_similarity(p1, p2)

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/suspect_images/<filename>")
def serve_suspect_image(filename):
    return send_from_directory(IMAGES_FOLDER, filename)

@app.route("/api/match", methods=["POST"])
def match_suspect():
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image uploaded."}), 400
    file = request.files["image"]
    if not file.filename or not allowed_file(file.filename):
        return jsonify({"success": False, "error": "Invalid file."}), 400

    ext  = file.filename.rsplit(".", 1)[1].lower()
    path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4().hex}.{ext}")
    file.save(path)
    print(f"[INFO] Saved: {path}")

    # ── Gender filter — from user selection ──────────────────────────────────
    gender_filter = request.form.get("gender", "any").strip()
    if gender_filter == "any":
        gender_filter = None
    print(f"[INFO] Gender filter: {gender_filter or 'none (showing all)'}")

    try:
        df = load_database()
    except FileNotFoundError as e:
        return jsonify({"success": False, "error": str(e)}), 500

    engine = "DeepFace/Facenet" if DEEPFACE_AVAILABLE else "ORB keypoint matching"
    print(f"[INFO] Engine: {engine} | Suspects: {len(df)}")

    scores = []
    for _, row in df.iterrows():
        name      = row.get("Name", "?")
        db_gender = row.get("Gender", "N/A").strip()

        # Skip if gender doesn't match
        if gender_filter and db_gender != "N/A" and db_gender != gender_filter:
            continue

        img_file = row.get("Image_File", "")
        img_path = os.path.join(IMAGES_FOLDER, img_file)
        if not os.path.exists(img_path):
            print(f"  [SKIP] {name} — image missing")
            continue

        score = compare_faces(path, img_path)
        if score is not None:
            print(f"  {name:30s} {score}%")
            scores.append((score, row, img_file))

    try:
        os.remove(path)
    except Exception:
        pass

    scores.sort(key=lambda x: x[0], reverse=True)

    matches = [{
        "id":            r.get("ID", "N/A"),
        "name":          r.get("Name", "N/A"),
        "age":           r.get("Age", "N/A"),
        "gender":        r.get("Gender", "N/A"),
        "address":       r.get("Address", "N/A"),
        "city":          r.get("City", "N/A"),
        "state":         r.get("State", "N/A"),
        "phone":         r.get("Phone", "N/A"),
        "aadhaar":       r.get("Aadhaar", "N/A"),
        "crime_history": r.get("Crime_History", "N/A"),
        "image_file":    imgf,
        "similarity":    sc,
    } for sc, r, imgf in scores[:TOP_N_RESULTS]]

    if matches:
        print(f"[INFO] Top: {matches[0]['name']} {matches[0]['similarity']}%")
    return jsonify({"success": True, "total_found": len(matches), "threshold": 0, "matches": matches})

@app.route("/api/database", methods=["GET"])
def get_database():
    try:
        df = load_database()
        return jsonify({"success": True, "count": len(df), "records": df.to_dict(orient="records")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    print("=" * 60)
    print("  Shodh- Starting")
    print(f"  Engine : {'DeepFace/Facenet' if DEEPFACE_AVAILABLE else 'ORB keypoint matching'}")
    print("  Open   : http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)
