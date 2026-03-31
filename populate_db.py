import requests
import pandas as pd
import os
import time

API_KEY    = "21179022e1189af8a8947d6204377bec"
BASE_URL   = "https://api.themoviedb.org/3"
IMG_BASE   = "https://image.tmdb.org/t/p/w500"
IMG_FOLDER = "suspect_images"
CSV_PATH   = "database/suspects.csv"

os.makedirs(IMG_FOLDER, exist_ok=True)

# ── 200+ actors across all industries ─────────────────────────────────────────
ACTORS = [
    # ── Bollywood ──────────────────────────────────────────────────────────────
    "Amitabh Bachchan", "Shah Rukh Khan", "Salman Khan", "Aamir Khan",
    "Hrithik Roshan", "Ranveer Singh", "Ranbir Kapoor", "Akshay Kumar",
    "Ajay Devgn", "Shahid Kapoor", "Varun Dhawan", "Tiger Shroff",
    "Anil Kapoor", "Sunny Deol", "Bobby Deol", "Sanjay Dutt",
    "Irrfan Khan", "Nawazuddin Siddiqui", "Rajkummar Rao", "Ayushmann Khurrana",
    "Vicky Kaushal", "Kartik Aaryan", "Sidharth Malhotra", "John Abraham",
    "Emraan Hashmi", "Arjun Kapoor", "Abhishek Bachchan", "Saif Ali Khan",
    # Bollywood Actresses
    "Deepika Padukone", "Priyanka Chopra", "Alia Bhatt", "Katrina Kaif",
    "Anushka Sharma", "Kareena Kapoor", "Kangana Ranaut", "Vidya Balan",
    "Taapsee Pannu", "Kriti Sanon", "Sara Ali Khan", "Janhvi Kapoor",
    "Shraddha Kapoor", "Sonam Kapoor", "Parineeti Chopra", "Yami Gautam",
    "Kiara Advani", "Nora Fatehi", "Disha Patani", "Malaika Arora",
    "Madhuri Dixit", "Kajol", "Rani Mukerji", "Preity Zinta",

    # ── Tollywood (Telugu) ─────────────────────────────────────────────────────
    "Prabhas", "Allu Arjun", "Mahesh Babu", "Jr NTR", "Ram Charan",
    "Vijay Deverakonda", "Nani", "Rana Daggubati", "Chiranjeevi", "Nagarjuna",
    "Venkatesh Daggubati", "Balakrishna", "Sai Dharam Tej", "Adivi Sesh",
    "Tovino Thomas", "Fahadh Faasil",
    # Telugu Actresses
    "Samantha Ruth Prabhu", "Rashmika Mandanna", "Pooja Hegde", "Kajal Aggarwal",
    "Tamannaah Bhatia", "Anupama Parameswaran", "Keerthy Suresh", "Sai Pallavi",

    # ── Kollywood (Tamil) ──────────────────────────────────────────────────────
    "Vijay", "Ajith Kumar", "Rajinikanth", "Dhanush", "Vikram",
    "Suriya", "Karthi", "Sivakarthikeyan", "Vishal", "Jayam Ravi",
    # Tamil Actresses
    "Nayanthara", "Trisha Krishnan", "Aishwarya Rajesh",

    # ── Marathi Cinema ─────────────────────────────────────────────────────────
    "Nana Patekar", "Sachin Pilgaonkar", "Ankush Chaudhari", "Bharat Jadhav",
    "Amey Wagh", "Subodh Bhave", "Sharad Ponkshe", "Upendra Limaye",
    # Marathi Actresses
    "Sai Tamhankar", "Priya Bapat", "Sonalee Kulkarni", "Spruha Joshi",
    "Amruta Khanvilkar", "Urmila Kanetkar", "Shruti Marathe",

    # ── Kannada Cinema ─────────────────────────────────────────────────────────
    "Yash", "Darshan Thoogudeepa", "Sudeep", "Puneeth Rajkumar",
    "Rishab Shetty", "Rakshit Shetty",

    # ── Malayalam Cinema ───────────────────────────────────────────────────────
    "Mohanlal", "Mammootty", "Dulquer Salmaan", "Prithviraj Sukumaran",
    "Nivin Pauly", "Asif Ali", "Jayasurya",

    # ── Bollywood / Crossover Directors (recognizable faces) ──────────────────
    "Amitabh Bachchan",

    # ── Hollywood ──────────────────────────────────────────────────────────────
    "Tom Cruise", "Leonardo DiCaprio", "Scarlett Johansson", "Dwayne Johnson",
    "Robert Downey Jr", "Chris Evans", "Chris Hemsworth", "Chris Pratt",
    "Brad Pitt", "Will Smith", "Tom Hanks", "Johnny Depp",
    "Keanu Reeves", "Ryan Reynolds", "Hugh Jackman", "Matt Damon",
    "Benedict Cumberbatch", "Mark Ruffalo", "Jeremy Renner", "Paul Rudd",
    "Zendaya", "Margot Robbie", "Jennifer Lawrence", "Emma Stone",
    "Anne Hathaway", "Cate Blanchett", "Natalie Portman", "Angelina Jolie",
    "Meryl Streep", "Sandra Bullock", "Reese Witherspoon", "Charlize Theron",
    "Gal Gadot", "Brie Larson", "Elizabeth Olsen", "Florence Pugh",
    "Denzel Washington", "Morgan Freeman", "Samuel L Jackson", "Idris Elba",
    "Viola Davis", "Lupita Nyongo",

    # ── International / South Korean ──────────────────────────────────────────
    "Lee Min-ho", "Park Seo-jun", "Song Joong-ki",
]

# Remove duplicates while preserving order
seen = set()
ACTORS_CLEAN = []
for a in ACTORS:
    if a not in seen:
        seen.add(a)
        ACTORS_CLEAN.append(a)

print(f"Total actors to fetch: {len(ACTORS_CLEAN)}")
print("=" * 50)

# ── Load existing CSV to avoid duplicates ──────────────────────────────────────
existing_names = set()
if os.path.exists(CSV_PATH):
    existing_df  = pd.read_csv(CSV_PATH, dtype=str)
    existing_names = set(existing_df["Name"].str.strip().tolist())
    records      = existing_df.to_dict(orient="records")
    start_id     = len(records) + 1000
    print(f"Found {len(existing_names)} existing records — will skip duplicates\n")
else:
    records  = []
    start_id = 1000

# ── Fetch and download ─────────────────────────────────────────────────────────
new_count = 0
skip_count = 0
fail_count = 0

for i, name in enumerate(ACTORS_CLEAN):

    if name in existing_names:
        print(f"  [SKIP] {name} already in database")
        skip_count += 1
        continue

    print(f"[{i+1}/{len(ACTORS_CLEAN)}] Fetching {name}...")

    try:
        search = requests.get(
            f"{BASE_URL}/search/person",
            params={"api_key": API_KEY, "query": name},
            timeout=10
        ).json()

        if not search.get("results"):
            print(f"  [NOT FOUND] {name}")
            fail_count += 1
            continue

        person     = search["results"][0]
        person_id  = person["id"]
        photo_path = person.get("profile_path", "")

        details = requests.get(
            f"{BASE_URL}/person/{person_id}",
            params={"api_key": API_KEY},
            timeout=10
        ).json()

        # ── Determine industry from known birthplace / popularity ──────────────
        birthplace = details.get("place_of_birth", "") or ""
        known_for  = [k.get("original_language","") for k in details.get("known_for", [])]
        if "hi" in known_for:       industry = "Bollywood"
        elif "te" in known_for:     industry = "Tollywood"
        elif "ta" in known_for:     industry = "Kollywood"
        elif "ml" in known_for:     industry = "Mollywood"
        elif "kn" in known_for:     industry = "Sandalwood"
        elif "mr" in known_for:     industry = "Marathi"
        elif "ko" in known_for:     industry = "Korean"
        else:                       industry = "Hollywood"

        # ── Download photo ─────────────────────────────────────────────────────
        img_filename = ""
        if photo_path:
            img_url      = IMG_BASE + photo_path
            img_filename = name.lower().replace(" ", "_").replace("-", "_") + ".jpg"
            img_path     = os.path.join(IMG_FOLDER, img_filename)

            if os.path.exists(img_path):
                print(f"  [EXISTS] Photo already downloaded")
            else:
                img_response = requests.get(img_url, timeout=15)
                if img_response.status_code == 200:
                    with open(img_path, "wb") as f:
                        f.write(img_response.content)
                    print(f"  Downloaded: {img_filename}")
                else:
                    print(f"  [WARN] Photo download failed: {img_response.status_code}")
                    img_filename = ""

        # ── Gender ─────────────────────────────────────────────────────────────
        gender_code = details.get("gender", 0)
        gender = "Male" if gender_code == 2 else "Female" if gender_code == 1 else "N/A"

        # ── Build record ───────────────────────────────────────────────────────
        records.append({
            "ID":            f"ID{start_id + new_count}",
            "Name":          details.get("name", name),
            "Age":           "",
            "Gender":        gender,
            "Industry":      industry,
            "Address":       "N/A",
            "City":          birthplace.split(",")[-1].strip() if birthplace else "N/A",
            "State":         "N/A",
            "Phone":         "N/A",
            "Aadhaar":       "N/A",
            "Crime_History": "None",
            "Image_File":    img_filename,
        })
        existing_names.add(name)
        new_count += 1

    except Exception as e:
        print(f"  [ERROR] {name}: {e}")
        fail_count += 1

    time.sleep(0.25)

# ── Save ───────────────────────────────────────────────────────────────────────
df = pd.DataFrame(records)
df.to_csv(CSV_PATH, index=False)

print("\n" + "=" * 50)
print(f"  Total in database : {len(records)}")
print(f"  Newly added       : {new_count}")
print(f"  Skipped (exists)  : {skip_count}")
print(f"  Failed / not found: {fail_count}")
print(f"  CSV saved to      : {CSV_PATH}")
print(f"  Photos saved to   : {IMG_FOLDER}/")
print("=" * 50)
print("\nNow run:  python app.py")
