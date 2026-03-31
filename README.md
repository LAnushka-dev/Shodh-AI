# 🔍 Shodh — Sketch Based Suspect Matching System

> Developed by **Anushka Londhe**

Shodh is an AI-powered forensic tool that matches pencil sketches or suspect photos against a criminal database using face recognition. Built for law enforcement use.

---

## 📋 Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running the App](#running-the-app)
- [Expanding the Database](#expanding-the-database)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

- Upload a **pencil sketch**, **CCTV screenshot**, or **photo** of a suspect
- Matches against a **local criminal database** using face recognition
- **Gender filter** — select Male / Female to narrow down results
- **Top 8 matches** ranked by similarity percentage
- Full suspect details in a **modal popup** (ID, age, address, crime history)
- **Auto-expands database** via TMDB API — download 200+ celebrity faces in one command
- Works **fully offline** after setup (no cloud API needed for matching)
- Neural matching via **DeepFace/Facenet** when weights are available
- Falls back to **ORB keypoint matching** if DeepFace is unavailable

---

## 📁 Project Structure

```
forensic.ai/
│
├── app.py                  # Main Flask backend
├── expand_database.py      # TMDB database expander script
├── download_weights.py     # DeepFace weights downloader
│
├── database/
│   └── suspects.csv        # Suspect records (ID, Name, Gender, etc.)
│
├── suspect_images/         # Suspect photos (.jpg)
│
├── uploads/                # Temporary upload folder (auto-cleaned)
│
├── templates/
│   └── index.html          # Frontend HTML
│
├── static/
│   ├── style.css           # Stylesheet
│   └── script.js           # Frontend logic
│
└── venv/                   # Python virtual environment
```

---

## ⚙️ Requirements

- Python 3.10+
- pip
- Internet connection (for first-time DeepFace weight download)

### Python Packages
```
flask
opencv-python
numpy
pandas
requests
deepface
tensorflow
```

---

## 🚀 Installation

### Step 1 — Clone or download the project
Place all files in a folder, e.g. `D:\forensic.ai\`

### Step 2 — Create virtual environment
```bash
cd D:\forensic.ai
python -m venv venv
```

### Step 3 — Activate virtual environment
```bash
venv\Scripts\activate.bat
```

### Step 4 — Install dependencies
```bash
pip install flask opencv-python numpy pandas requests deepface tensorflow
```

### Step 5 — Download DeepFace weights (for accurate matching)
```bash
python download_weights.py
```
This downloads the Facenet model (~92 MB) once. After this, matching works offline.

---

## ▶️ Running the App

**Always activate venv first:**
```bash
d:\forensic.ai\venv\Scripts\activate.bat
python app.py
```

Then open your browser and go to:
```
http://localhost:5000
```

---

## 🗄️ Expanding the Database

To add 200+ celebrities from TMDB automatically:

```bash
python expand_database.py
```

- Downloads photos into `suspect_images\`
- Adds records to `suspects.csv`
- Skips anyone already in the database
- Change `PAGES = 10` to `PAGES = 25` in the file for ~500 people

To add your own suspect manually, add a row to `suspects.csv`:
```
ID1100,John Doe,,Male,123 Main St,Mumbai,Maharashtra,N/A,N/A,Theft,john_doe.jpg
```
And place `john_doe.jpg` in `suspect_images\`.

---

## 🧠 How It Works

```
User uploads sketch / photo
        ↓
Gender filter applied (Male / Female / Any)
        ↓
Face compared against each suspect in database
        ↓
DeepFace/Facenet (neural) → most accurate
   OR ORB keypoint matching → fallback
        ↓
Top 8 matches ranked by similarity %
        ↓
Results displayed with full suspect details
```

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'cv2'` | Activate venv first: `venv\Scripts\activate.bat` |
| `No strong matches found` | Run `python download_weights.py` to fix DeepFace |
| Wrong gender showing in results | Select ♂ Male or ♀ Female in the UI before running |
| `Database not found` | Make sure `database\suspects.csv` exists |
| `Connection error` | Flask server isn't running — run `python app.py` |
| Port 5000 already in use | Kill old process or change port in `app.py` to `5001` |

---

## 👩‍💻 Developer

**Anushka Londhe**

> ⚠️ This tool is intended for **law enforcement and academic purposes only**.  
> All matches are shortlisted suspects and require full investigation before any action is taken.
